import asyncio
from app.db.session import AsyncSessionLocal
from app.models.food import Food
from app.services.embedding_service import get_embedding

# USDA-verified ingredients (per 100g), manually cross-checked for realistic values
INGREDIENTS_DATA = [
    {
        "name": "Rice (cooked)",
        "fdc_id": 2708408,
        "calories_per_100g": 129, "protein_per_100g": 2.67, "carbs_per_100g": 27.99, "fats_per_100g": 0.28,
    },
    {
        "name": "Whole wheat flour",
        "fdc_id": 168944,
        "calories_per_100g": 332, "protein_per_100g": 9.61, "carbs_per_100g": 74.5, "fats_per_100g": 1.95,
    },
    {
        "name": "Lentils/Daal (cooked)",
        "fdc_id": 175254,
        "calories_per_100g": 114, "protein_per_100g": 9.02, "carbs_per_100g": 19.5, "fats_per_100g": 0.38,
    },
    {
        "name": "Chicken breast (cooked)",
        "fdc_id": 171140,
        "calories_per_100g": 157, "protein_per_100g": 32.1, "carbs_per_100g": 0, "fats_per_100g": 3.24,
    },
    {
        "name": "Whole milk",
        "fdc_id": 1939139,
        "calories_per_100g": 67, "protein_per_100g": 3.33, "carbs_per_100g": 4.58, "fats_per_100g": 3.75,
    },
]

# South Asian dishes composed from the above verified ingredients + typical serving sizes
DISHES_DATA = [
    {
        "name": "Roti",
        "description": "1 medium roti, whole wheat, approximately 40g cooked dough (from ~30g flour)",
        "base_ingredient": "Whole wheat flour", "grams": 30,
    },
    {
        "name": "Daal (1 katori)",
        "description": "1 katori (bowl) cooked lentils, approximately 150g",
        "base_ingredient": "Lentils/Daal (cooked)", "grams": 150,
    },
    {
        "name": "White Rice (1 cup cooked)",
        "description": "1 cup cooked white rice, approximately 150g",
        "base_ingredient": "Rice (cooked)", "grams": 150,
    },
    {
        "name": "Grilled Chicken Breast",
        "description": "1 serving grilled/cooked chicken breast, approximately 150g, no oil/batter",
        "base_ingredient": "Chicken breast (cooked)", "grams": 150,
    },
    {
        "name": "Glass of Milk",
        "description": "1 glass whole milk, approximately 250ml",
        "base_ingredient": "Whole milk", "grams": 250,
    },
]


def scale_nutrition(ingredient: dict, grams: float) -> dict:
    factor = grams / 100
    return {
        "calories": round(ingredient["calories_per_100g"] * factor, 1),
        "protein_g": round(ingredient["protein_per_100g"] * factor, 1),
        "carbs_g": round(ingredient["carbs_per_100g"] * factor, 1),
        "fats_g": round(ingredient["fats_per_100g"] * factor, 1),
    }


async def seed_foods():
    ingredients_by_name = {item["name"]: item for item in INGREDIENTS_DATA}

    async with AsyncSessionLocal() as db:
        for dish in DISHES_DATA:
            ingredient = ingredients_by_name[dish["base_ingredient"]]
            nutrition = scale_nutrition(ingredient, dish["grams"])

            embedding_text = f"{dish['name']}: {dish['description']}"
            embedding = await get_embedding(embedding_text)

            food = Food(
                name=dish["name"],
                description=dish["description"],
                calories=nutrition["calories"],
                protein_g=nutrition["protein_g"],
                carbs_g=nutrition["carbs_g"],
                fats_g=nutrition["fats_g"],
                embedding=embedding,
            )
            db.add(food)
            print(f"Added: {dish['name']} -> {nutrition}")

        await db.commit()
    print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_foods())