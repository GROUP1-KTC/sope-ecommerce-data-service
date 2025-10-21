from typing import TypedDict, Annotated, Sequence, Literal, Optional, List, Dict, Any
import operator
import json
import logging

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, END

from app.features.chatbot.agent.tools import get_tools
from app.features.chatbot.llm.bedrock_client import get_bedrock_client
from app.features.chatbot.agent.system_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_token: str
    session_id: str


class ReActChatbotGraph:
    """
    ReAct agent wired for:
    - LLM-based routing (no keyword branching)
    - Tool loops (agent can call tools multiple times)
    - RAG/tool integration inside the loop
    """

    def __init__(self, user_token: Optional[str] = None):
        self.llm = get_bedrock_client()
        tools_list = get_tools(user_token)
        self.tools = {tool.name: tool for tool in tools_list}
        self.llm_with_tools = self.llm.bind_tools(tools_list)
        self.user_token = user_token
        print(f"[ReActChatbotGraph] Initialized with user_token: {user_token}")
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._take_action)
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self._next_step,
            {
                "continue": "tools",
                "end": END,
            },
        )
        workflow.add_edge("tools", "agent")
        return workflow.compile()

    async def _agent_node(self, state: AgentState) -> AgentState:
        """
        Let the LLM decide whether to respond or call tools.
        Uses optimized system prompt with clear tool guidelines and examples.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *state["messages"],
        ]

        response = await self.llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    async def _take_action(self, state: AgentState) -> AgentState:
        """
        Execute tool calls returned by the LLM and append results.
        Auto-injects user_token into authenticated tools.
        ALWAYS uses real user_token from state, NEVER what LLM sends.
        """
        tool_calls = state["messages"][-1].tool_calls
        tool_results: list[ToolMessage] = []
        
        # Auth-required tools that need user_token
        auth_required_tools = {"list_orders", "track_order", "add_item_to_cart"}
        
        # Get real user_token from state (not from LLM)
        real_user_token = state.get("user_token")

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"].copy()
            
            # FORCE-INJECT real user_token for authenticated tools
            # Always override what LLM sent, use real token from state
            if tool_name in auth_required_tools:
                if real_user_token:
                    tool_args["user_token"] = real_user_token
                    print(f"[AGENT] ✅ Force-injected REAL user_token into {tool_name}")
                else:
                    print(f"[AGENT] ⚠️  {tool_name} requires user_token but state has None")
            
            print(f"[AGENT] Executing tool: {tool_name} with args: {tool_args}")

            tool = self.tools.get(tool_name)
            if not tool:
                print(f"[AGENT] Tool {tool_name} not found")
                tool_results.append(
                    ToolMessage(
                        content=f"Không tìm thấy tool '{tool_name}' ",
                        tool_call_id=tool_call["id"],
                        name=tool_name,
                    )
                )
                continue

            try:
                result = await tool.ainvoke(tool_args)
                try:
                    serialized = json.dumps(result, ensure_ascii=False, default=str)
                except TypeError:
                    serialized = json.dumps({"data": result}, ensure_ascii=False, default=str)
                print(f"[AGENT] Tool {tool_name} returned: {serialized[:200]}...")
                tool_results.append(
                    ToolMessage(
                        content=serialized,
                        tool_call_id=tool_call["id"],
                        name=tool_name,
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive
                print(f"[AGENT] Tool {tool_name} raised exception: {exc}")
                tool_results.append(
                    ToolMessage(
                        content=f"Error executing {tool_name}: {exc}",
                        tool_call_id=tool_call["id"],
                        name=tool_name,
                    )
                )

        return {"messages": tool_results}

    def _next_step(self, state: AgentState) -> Literal["continue", "end"]:
        """
        Decide whether to loop back to tools or finish with a final answer.
        """
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        return "end"

    async def run(
        self,
        message: str,
        session_id: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> dict:
        """Run the ReAct graph and return the final agent response."""
        initial_messages: List[BaseMessage] = []
        if history:
            for entry in history:
                role = entry.get("role")
                content = entry.get("content", "")
                if role == "user":
                    initial_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    initial_messages.append(AIMessage(content=content))
                elif role == "tool":
                    name = entry.get("name")
                    tool_call_id = entry.get("tool_call_id") or f"cached_{name or 'tool'}"
                    initial_messages.append(
                        ToolMessage(
                            content=content,
                            name=name,
                            tool_call_id=tool_call_id,
                        )
                    )

        initial_messages.append(HumanMessage(content=message))

        initial_state: AgentState = {
            "messages": initial_messages,
            "user_token": self.user_token,
            "session_id": session_id,
        }

        result = await self.graph.ainvoke(initial_state, config={"recursion_limit": 10})
        final_message = result["messages"][-1]

        tool_calls: list[str] = []
        tool_outputs: List[Dict[str, Any]] = []
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls.extend(tc["name"] for tc in msg.tool_calls)
            if isinstance(msg, ToolMessage):
                try:
                    payload = json.loads(msg.content)
                except (json.JSONDecodeError, TypeError):
                    payload = msg.content
                tool_outputs.append(
                    {
                        "name": getattr(msg, "name", None),
                        "output": payload,
                        "tool_call_id": getattr(msg, "tool_call_id", None),
                    }
                )

        return {
            "response": final_message.content,
            "tool_calls": tool_calls,
            "message_count": len(result["messages"]),
            "tool_outputs": tool_outputs,
        }
