from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import Food
from app.services.embedding_service import get_embedding


async def retrieve_similar_foods(db: AsyncSession, query_text: str, limit: int = 3) -> list[Food]:
    """Query text ko embed karo, phir cosine distance se sabse similar foods DB se nikalo"""
    query_embedding = await get_embedding(query_text)

    result = await db.execute(
        select(Food)
        .order_by(Food.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    return list(result.scalars().all())