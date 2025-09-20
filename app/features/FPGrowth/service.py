import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules
from mlxtend.preprocessing import TransactionEncoder


class FPGrowthRecommender:
    def __init__(self, pool):
        self.pool = pool

    @classmethod
    async def from_pretrained(cls, pool=None):
        if pool is None:
            raise ValueError(
                "Database pool is required to initialize FPGrowthRecommender."
            )
        return cls(pool)

    async def get_transactions(self, min_items: int = 0):
        """Get list of transactions (each transaction = list product_id)."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT o.order_id, array_agg(p.product_id::text) AS products
                FROM order_items oi
                JOIN orders o ON o.order_id = oi.order_id
                JOIN product_variants pv ON pv.product_variant_id = oi.product_variant_id
                JOIN products p ON p.product_id = pv.product_id
                GROUP BY o.order_id
                HAVING COUNT(oi.product_variant_id) >= $1;
            """,
                min_items,
            )
            return [row["products"] for row in rows]

    def mine_rules(self, transactions, min_support=0.05, min_confidence=0.2):
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        df = pd.DataFrame(te_ary, columns=te.columns_)

        frequent_itemsets = fpgrowth(df, min_support=min_support, use_colnames=True)
        rules = association_rules(
            frequent_itemsets, metric="confidence", min_threshold=min_confidence
        )
        return rules

    def recommend_from_rules(self, product_id, rules, top_n=5):
        """
        Lấy top-N gợi ý cho product_id dựa trên rules.
        """
        target_rules = rules[
            rules["antecedents"].apply(lambda x: product_id in list(x))
        ]
        rec_scores = {}
        for _, row in target_rules.iterrows():
            for cons in row["consequents"]:
                if cons != product_id:
                    rec_scores[cons] = rec_scores.get(cons, 0) + row["confidence"]

        top_recs = sorted(rec_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [{"product_id": rid} for rid, _ in top_recs]

    async def recommend(
        self,
        product_id: str,
        top_n: int = 5,
        min_support: float = 0.05,
        min_confidence: float = 0.2,
    ):
        """Recommend products based on FPGrowth rules."""
        transactions = await self.get_transactions()
        if not transactions:
            return []

        rules = self.mine_rules(transactions, min_support, min_confidence)

        return self.recommend_from_rules(product_id, rules, top_n)

    async def update_suggested_products_in_db(
        self, top_n=5, min_support=0.05, min_confidence=0.2
    ):
        """update all suggested products in DB"""

        transactions = await self.get_transactions()
        if not transactions:
            return

        rules = self.mine_rules(transactions, min_support, min_confidence)

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("TRUNCATE TABLE product_suggestions")

                rows = await conn.fetch("SELECT product_id FROM products")
                all_products = [row["product_id"] for row in rows]

                for pid in all_products:
                    recs = self.recommend_from_rules(str(pid), rules, top_n)
                    for r in recs:
                        await conn.execute(
                            """
                            INSERT INTO product_suggestions (product_id, suggested_product_id)
                            VALUES ($1, $2)
                        """,
                            str(pid),
                            str(r["product_id"]),
                        )

        print("Updated all suggested products in DB successfully.")
