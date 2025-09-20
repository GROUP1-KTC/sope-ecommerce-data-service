import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np

import faiss


class ContentRecommender:
    def __init__(self, model_name: str = None, top_n: int = 5, pool=None):
        self.model = SentenceTransformer(model_name)
        self.products = None
        self.pool = pool
        self.embeddings = None
        self.index = None
        self.top_n = top_n

    @classmethod
    async def from_pretrained(cls, model_name="all-MiniLM-L6-v2", pool=None):
        if pool is None:
            raise ValueError("Database pool must be provided for ContentRecommender.")

        if model_name is None:
            raise ValueError("model_name must be provided")
        self = cls(model_name=model_name, pool=pool)

        self.products = await self.load_products()

        texts = (
            self.products["name"].fillna("")
            + " "
            + self.products["brand"].fillna("")
            + " "
            + self.products["description"].fillna("")
        )

        self.embeddings = self.model.encode(
            texts.tolist(),
            convert_to_tensor=False,
            batch_size=64,
            show_progress_bar=True,
        ).astype("float32")

        self.embeddings = self.embeddings / np.linalg.norm(
            self.embeddings, axis=1, keepdims=True
        )

        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(self.embeddings)

        return self

    async def load_products(self):
        """Load toàn bộ product từ DB"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT product_id, name, brand, description FROM products"
            )

            df = pd.DataFrame([dict(r) for r in rows])
            df["product_id"] = df["product_id"].astype(str)
            return df

    def recommend(self, product_id, top_n=None):
        """get top_n similar products based on cosine similarity"""
        if product_id not in self.products["product_id"].values:
            return []

        if top_n is None:
            top_n = self.top_n

        idx = self.products.index[self.products["product_id"] == product_id][0]
        query_vec = self.embeddings[idx].reshape(1, -1)

        _, indices = self.index.search(query_vec, top_n + 1)

        rec_indices = [i for i in indices[0] if i != idx][:top_n]

        return self.products.iloc[rec_indices][["product_id"]].to_dict(orient="records")

    async def update_similar_products_in_db(self, top_n=None):
        """Cập nhật bảng product_similarities"""
        if top_n is None:
            top_n = self.top_n

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("TRUNCATE TABLE product_similarities")

                for _, row in self.products.iterrows():
                    product_id = row["product_id"]
                    recs = self.recommend(product_id, top_n=top_n)
                    rec_ids = [r["product_id"] for r in recs]

                    values = [
                        (str(product_id), str(similar_id)) for similar_id in rec_ids
                    ]
                    if values:
                        await conn.executemany(
                            """
                            INSERT INTO product_similarities (product_id, similar_product_id)
                            VALUES ($1, $2)
                            """,
                            values,
                        )
        print("Updated all product similarities using FAISS successfully.")
