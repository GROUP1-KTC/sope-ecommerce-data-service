import numpy as np
from scipy.stats import pearsonr
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict


class UserCFRecommender:
    def __init__(self, pool):
        self.pool = pool
        self.all_categories = []
        self.all_brands = []

    @classmethod
    async def from_pretrained(cls, pool=None):
        if pool is None:
            raise ValueError("Database pool must be provided for UserCFRecommender.")
        instance = cls(pool)

        await instance._load_dimensions()
        return instance

    async def _load_dimensions(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT name FROM categories;")
            self.all_categories = sorted([row["name"] for row in rows])

            rows = await conn.fetch("SELECT DISTINCT brand FROM products WHERE status = 'APPROVED';")
            self.all_brands = sorted([row["brand"] for row in rows])

    async def _create_user_profiles(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, username, email FROM users;")
            users = [
                {"id": row["id"], "username": row["username"], "email": row["email"]}
                for row in rows
            ]

            profiles = []
            for user in users:
                profile = {
                    "user_id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "order_count": 0,
                    "total_spent": 0.0,
                    "categories": {cat: 0 for cat in self.all_categories},
                    "brand_preferences": {brand: 0 for brand in self.all_brands},
                }

                orders = await conn.fetch(
                    "SELECT o.order_id, o.total_amount FROM orders o WHERE o.user_id = $1;",
                    user["id"],
                )
                profile["order_count"] = len(orders)

                for order in orders:
                    profile["total_spent"] += float(order["total_amount"])

                    items = await conn.fetch(
                        """
                        SELECT p.product_id, p.brand, c.name, oi.quantity
                        FROM order_items oi
                        JOIN product_variants pv ON pv.product_variant_id = oi.product_variant_id
                        JOIN products p ON p.product_id = pv.product_id
                        JOIN categories c ON c.id = p.category_id
                        WHERE oi.order_id = $1
                        AND p.status = 'APPROVED';
                        """,
                        order["order_id"],
                    )

                    for row in items:
                        brand, category_name, qty = (
                            row["brand"],
                            row["category_name"],
                            row["quantity"],
                        )

                        if category_name in profile["categories"]:
                            profile["categories"][category_name] += qty
                        if brand in profile["brand_preferences"]:
                            profile["brand_preferences"][brand] += qty

                profiles.append(profile)
            return profiles

    def _profile_to_vector(self, profile):
        vector = [profile["order_count"], profile["total_spent"]]
        vector.extend(profile["categories"][cat] for cat in self.all_categories)
        vector.extend(profile["brand_preferences"][brand] for brand in self.all_brands)
        return np.array(vector, dtype=float)

    def _compute_similarity(self, target_vector, other_vectors):
        pearson_scores, cosine_scores = [], []
        for v in other_vectors:
            if np.std(target_vector) == 0 or np.std(v) == 0:
                p_score = 0.0
            else:
                p_score, _ = pearsonr(target_vector, v)
                if np.isnan(p_score):
                    p_score = 0.0
            pearson_scores.append(p_score)
            cosine_scores.append(cosine_similarity([target_vector], [v])[0][0])
        return pearson_scores, cosine_scores

    def _find_top_similar_users(self, target_profile, profiles, n=5):
        target_vector = self._profile_to_vector(target_profile)
        other_profiles = [
            p for p in profiles if p["user_id"] != target_profile["user_id"]
        ]
        other_vectors = [self._profile_to_vector(p) for p in other_profiles]

        pearson_scores, cosine_scores = self._compute_similarity(
            target_vector, other_vectors
        )
        combined_scores = [
            (0.5 * p + 0.5 * c, idx)
            for idx, (p, c) in enumerate(zip(pearson_scores, cosine_scores))
        ]
        combined_scores.sort(reverse=True)
        top_indices = [idx for _, idx in combined_scores[:n]]
        return [(other_profiles[idx], combined_scores[idx][0]) for idx in top_indices]

    async def _get_purchased_products(self, user_id):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT p.product_id
                FROM order_items oi
                JOIN product_variants pv ON pv.product_variant_id = oi.product_variant_id
                JOIN products p ON p.product_id = pv.product_id
                JOIN orders o ON o.order_id = oi.order_id
                WHERE o.user_id = $1
                AND p.status = 'APPROVED';
                """,
                user_id,
            )
            return set(row["product_id"] for row in rows)

    async def recommend_products(self, target_user_id, top_n=5):
        profiles = await self._create_user_profiles()
        target_profile = next(
            (p for p in profiles if p["user_id"] == target_user_id), None
        )
        if not target_profile:
            return []

        similar_users = self._find_top_similar_users(target_profile, profiles, n=5)
        target_products = await self._get_purchased_products(target_user_id)

        product_scores = defaultdict(float)
        async with self.pool.acquire() as conn:
            for user, weight in similar_users:
                rows = await conn.fetch(
                    """
                    SELECT p.product_id, p.name, SUM(oi.quantity) as qty
                    FROM order_items oi
                    JOIN product_variants pv ON pv.product_variant_id = oi.product_variant_id
                    JOIN products p ON p.product_id = pv.product_id
                    JOIN orders o ON o.order_id = oi.order_id
                    WHERE o.user_id = $1
                    AND p.status = 'APPROVED'
                    GROUP BY p.product_id, p.name;
                    """,
                    user["user_id"],
                )
                for product_id, name, qty in rows:
                    if product_id not in target_products:
                        product_scores[(product_id, name)] += qty * weight

        sorted_products = sorted(
            product_scores.items(), key=lambda x: x[1], reverse=True
        )[:top_n]
        return [{"product_id": pid} for (pid, _), _ in sorted_products]

    async def update_suggested_products_for_all_users(self, top_n=5):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("TRUNCATE TABLE product_suggested_for_user")

                rows = await conn.fetch("SELECT id FROM users")
                all_users = [row["id"] for row in rows]

                insert_values = []

                for user_id in all_users:
                    recs = await self.recommend_products(user_id, top_n=top_n)
                    for r in recs:
                        # await conn.execute(
                        #     """
                        #     INSERT INTO product_suggested_for_user (user_id, product_id)
                        #     VALUES ($1, $2)
                        #     """,
                        #     str(user_id),
                        #     str(r["product_id"]),
                        # )

                        insert_values.append((str(user_id), str(r["product_id"])))

                if insert_values:
                    await conn.executemany(
                        "INSERT INTO product_suggested_for_user (user_id, product_id) VALUES ($1, $2)",
                        insert_values,
                    )

        print("All users' suggested products updated successfully.")
