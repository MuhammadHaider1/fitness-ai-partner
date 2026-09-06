import httpx

from app.core.config import settings

USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

async def search_usda_food(fdc_id:int) -> dict | None:
    """USDA database mein food dhoondo, best match ka basic nutrition data return karo"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{USDA_BASE_URL}/foods/{fdc_id}",
            params={"api_key":settings.USDA_API_KEY},
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("foods"):
            return None
        
        food = data["foods"][0]
        nutrients = {n["nutrientName"]: n["value"] for n in food.get("foodNutrients", [])}

        return {
            "fdc_id": food["fdcId"],
            "description": food["description"],
            "calories_per_100g": nutrients.get("Energy", 0),
            "protein_per_100g": nutrients.get("Protein", 0),
            "carbs_per_100g": nutrients.get("Carbohydrate, by difference", 0),
            "fats_per_100g": nutrients.get("Total lipid (fat)", 0),
        }