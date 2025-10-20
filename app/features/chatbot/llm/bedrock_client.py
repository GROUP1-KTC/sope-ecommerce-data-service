import boto3
from langchain_aws import ChatBedrock
from app.configs.settings import settings


class BedrockClient:
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id_chatbot,
            aws_secret_access_key=settings.aws_secret_access_key_chatbot
        )
        
        self.llm = ChatBedrock(
            model_id=settings.bedrock_model_id,
            client=self.bedrock_runtime,
            model_kwargs={
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2000,
            }
        )
    
    def get_llm(self):
        return self.llm


# Singleton instance
_bedrock_client_instance = None

def get_bedrock_client():
    """Get singleton Bedrock client"""
    global _bedrock_client_instance
    if _bedrock_client_instance is None:
        _bedrock_client_instance = BedrockClient()
    return _bedrock_client_instance.get_llm()
