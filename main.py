from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import openai
import os
import json
from dotenv import load_dotenv
from models import PantryItem, MealSuggestion, MultipleMealSuggestions, CalorieGoal

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory pantry (for initial prototyping)
pantry: List[PantryItem] = [
    PantryItem(
        name="Chicken Breast",
        quantity=2,
        unit="pieces",
        calories=165,
        protein=31,
        carbohydrates=0,
        sugars=0,
        fats=3.6,
        saturated_fat=1,
        fiber=0,
        sodium=74,
        serving_size=100,
        serving_unit="g"
    ),
    PantryItem(
        name="Brown Rice",
        quantity=500,
        unit="g",
        calories=112,
        protein=2.6,
        carbohydrates=23,
        sugars=0.4,
        fats=0.9,
        saturated_fat=0.2,
        fiber=1.8,
        sodium=5,
        serving_size=100,
        serving_unit="g"
    ),
    PantryItem(
        name="Broccoli",
        quantity=300,
        unit="g",
        calories=34,
        protein=2.8,
        carbohydrates=7,
        sugars=1.5,
        fats=0.4,
        saturated_fat=0.1,
        fiber=2.6,
        sodium=33,
        serving_size=100,
        serving_unit="g"
    ),
    PantryItem(
        name="Olive Oil",
        quantity=250,
        unit="ml",
        calories=884,
        protein=0,
        carbohydrates=0,
        sugars=0,
        fats=100,
        saturated_fat=13.8,
        fiber=0,
        sodium=2,
        serving_size=100,
        serving_unit="ml"
    ),
    PantryItem(
        name="Eggs",
        quantity=6,
        unit="pieces",
        calories=155,
        protein=13,
        carbohydrates=1.1,
        sugars=1.1,
        fats=11,
        saturated_fat=3.3,
        fiber=0,
        sodium=124,
        serving_size=100,
        serving_unit="g"
    ),
    PantryItem(
        name="Sweet Potato",
        quantity=3,
        unit="pieces",
        calories=86,
        protein=1.6,
        carbohydrates=20,
        sugars=4.2,
        fats=0.1,
        saturated_fat=0,
        fiber=3,
        sodium=5,
        serving_size=100,
        serving_unit="g"
    ),
    PantryItem(
        name="Salmon Fillet",
        quantity=1,
        unit="pieces",
        calories=208,
        protein=25,
        carbohydrates=0,
        sugars=0,
        fats=12,
        saturated_fat=3,
        fiber=0,
        sodium=59,
        serving_size=100,
        serving_unit="g"
    ),
    PantryItem(
        name="Spinach",
        quantity=200,
        unit="g",
        calories=23,
        protein=2.9,
        carbohydrates=3.6,
        sugars=0.4,
        fats=0.4,
        saturated_fat=0.1,
        fiber=2.2,
        sodium=79,
        serving_size=100,
        serving_unit="g"
    )
]

@app.get("/pantry", response_model=List[PantryItem])
def get_pantry():
    return pantry

@app.post("/pantry", response_model=PantryItem)
def add_pantry_item(item: PantryItem):
    pantry.append(item)
    return item

@app.put("/pantry/{item_name}", response_model=PantryItem)
def update_pantry_item(item_name: str, updated_item: PantryItem):
    global pantry
    # Find and replace the original item
    for i, item in enumerate(pantry):
        if item.name == item_name:
            pantry[i] = updated_item
            return updated_item
    # If original item not found, return error (shouldn't happen in normal flow)
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/pantry/{item_name}")
def delete_pantry_item(item_name: str):
    global pantry
    pantry = [item for item in pantry if item.name != item_name]
    return {"status": "deleted"}



def generate_ai_meal_suggestion(pantry_items: List[PantryItem], goal: CalorieGoal) -> MealSuggestion:
    """
    Generate AI-powered meal suggestion using OpenAI API
    """
    # Format pantry contents for the AI prompt
    pantry_text = "\n".join([
        f"- {item.name}: {item.quantity} {item.unit}" + 
        (f" (per {item.serving_size}{item.serving_unit}: {item.calories}kcal, {item.protein}g protein, {item.carbohydrates}g carbs, {item.fats}g fat)" 
         if item.calories else "")
        for item in pantry_items
    ])
    
    # Create the AI prompt
    prompt = f"""
You are a professional chef and nutritionist. Create a meal suggestion using ONLY the available ingredients from the pantry below.

AVAILABLE PANTRY INGREDIENTS:
{pantry_text}

NUTRITIONAL TARGETS:
- Calories: {goal.calories} kcal
- Protein: {goal.protein or 'flexible'} g
- Carbohydrates: {goal.carbs or 'flexible'} g
- Fats: {goal.fats or 'flexible'} g

IMPORTANT: Use the exact ingredient names and consider their available quantities from the pantry above. Create realistic portions that don't exceed what's available.

Please provide a meal suggestion in the following JSON format:
{{
    "title": "Creative Meal Name (e.g., 'Herb-Crusted Chicken with Garlic Rice')",
    "ingredients": ["[quantity][unit] [ingredient_name]", "[quantity][unit] [ingredient_name]"],
    "calories": estimated_calories_number,
    "protein": estimated_protein_grams,
    "carbs": estimated_carbs_grams,
    "fats": estimated_fats_grams,
    "steps": [
        "[Detailed cooking instruction with specific quantities]",
        "[Another detailed step with specific amounts]",
        "[Continue with clear steps including temperatures and timing]"
    ]
}}

CRITICAL REQUIREMENTS:
1. ALWAYS include specific quantities/weights for EVERY ingredient (e.g., "200g Chicken Breast", "150ml Olive Oil")
2. Use ONLY ingredients available in the pantry with their available quantities
3. In cooking steps, specify exact amounts for each ingredient used (e.g., "Cook 150g brown rice", "Add 15ml olive oil")
4. Try to meet the nutritional targets as closely as possible
5. Provide detailed, clear cooking instructions with specific temperatures and times
6. Make it a complete, balanced meal
7. Be creative but practical
8. Return ONLY valid JSON, no additional text
9. Ensure ingredient quantities don't exceed what's available in the pantry
"""
    
    try:
        # Get OpenAI API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            # Fallback meal suggestion if no API key
            return MealSuggestion(
                title="Simple Pantry Meal",
                ingredients=[item.name for item in pantry_items[:3]] if pantry_items else ["rice", "egg"],
                calories=goal.calories,
                protein=goal.protein or 20,
                carbs=goal.carbs or 45,
                fats=goal.fats or 15,
                steps=[
                    "Note: OpenAI API key not configured. This is a basic suggestion.",
                    "Combine available ingredients in a pan.",
                    "Cook on medium heat for 10-15 minutes.",
                    "Season to taste and serve hot."
                ]
            )
        
        # Create OpenAI client and call API
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional chef and nutritionist. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        # Parse the AI response
        ai_response = response.choices[0].message.content.strip()
        meal_data = json.loads(ai_response)
        
        return MealSuggestion(
            title=meal_data.get("title", "AI-Generated Meal"),
            ingredients=meal_data.get("ingredients", []),
            calories=meal_data.get("calories", goal.calories),
            protein=meal_data.get("protein", goal.protein or 0),
            carbs=meal_data.get("carbs", goal.carbs or 0),
            fats=meal_data.get("fats", goal.fats or 0),
            steps=meal_data.get("steps", [])
        )
        
    except Exception as e:
        # Fallback meal suggestion if AI fails
        available_ingredients = [item.name for item in pantry_items[:4]] if pantry_items else ["rice", "egg", "vegetables"]
        return MealSuggestion(
            title="Simple Pantry Meal",
            ingredients=available_ingredients,
            calories=goal.calories,
            protein=goal.protein or 20,
            carbs=goal.carbs or 45,
            fats=goal.fats or 15,
            steps=[
                f"AI generation failed ({str(e)}). Here's a basic suggestion:",
                f"Combine {', '.join(available_ingredients[:2])} in a large pan.",
                "Cook on medium heat, stirring occasionally.",
                "Add seasonings and cook until ingredients are tender.",
                "Serve hot and enjoy your meal!"
            ]
        )

def generate_multiple_ai_meals(pantry_items: List[PantryItem], goal: CalorieGoal, count: int = 3) -> List[MealSuggestion]:
    """
    Generate multiple AI-powered meal suggestions
    """
    meals = []
    
    # Format pantry contents for the AI prompt
    pantry_text = "\n".join([
        f"- {item.name}: {item.quantity} {item.unit}" + 
        (f" (per {item.serving_size}{item.serving_unit}: {item.calories}kcal, {item.protein}g protein, {item.carbohydrates}g carbs, {item.fats}g fat)" 
         if item.calories else "")
        for item in pantry_items
    ])
    
    # Create the AI prompt for multiple meals
    prompt = f"""
You are a professional chef and nutritionist. Create {count} different meal suggestions using ONLY the available ingredients from the pantry below.

AVAILABLE PANTRY INGREDIENTS:
{pantry_text}

NUTRITIONAL TARGETS:
- Calories: {goal.calories} kcal
- Protein: {goal.protein or 'flexible'} g
- Carbohydrates: {goal.carbs or 'flexible'} g
- Fats: {goal.fats or 'flexible'} g

IMPORTANT: Use the exact ingredient names and consider their available quantities from the pantry above. Create realistic portions that don't exceed what's available. Make each meal different and creative.

Please provide {count} meal suggestions in the following JSON format:
{{
    "meals": [
        {{
            "title": "Creative Meal Name 1",
            "ingredients": ["[quantity][unit] [ingredient_name]", "[quantity][unit] [ingredient_name]"],
            "calories": estimated_calories_number,
            "protein": estimated_protein_grams,
            "carbs": estimated_carbs_grams,
            "fats": estimated_fats_grams,
            "steps": [
                "[Detailed cooking instruction with specific quantities]",
                "[Another detailed step with specific amounts]"
            ]
        }},
        {{
            "title": "Creative Meal Name 2",
            "ingredients": ["[quantity][unit] [ingredient_name]", "[quantity][unit] [ingredient_name]"],
            "calories": estimated_calories_number,
            "protein": estimated_protein_grams,
            "carbs": estimated_carbs_grams,
            "fats": estimated_fats_grams,
            "steps": [
                "[Detailed cooking instruction with specific quantities]",
                "[Another detailed step with specific amounts]"
            ]
        }}
    ]
}}

CRITICAL REQUIREMENTS:
1. ALWAYS include specific quantities/weights for EVERY ingredient (e.g., "200g Chicken Breast", "150ml Olive Oil")
2. Use ONLY ingredients available in the pantry with their available quantities
3. In cooking steps, specify exact amounts for each ingredient used
4. Try to meet the nutritional targets as closely as possible
5. Provide detailed, clear cooking instructions with specific temperatures and times
6. Make each meal different and creative
7. Return ONLY valid JSON, no additional text
8. Ensure ingredient quantities don't exceed what's available in the pantry
"""
    
    try:
        # Get OpenAI API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            # Fallback multiple meal suggestions if no API key
            available_ingredients = [item.name for item in pantry_items[:4]] if pantry_items else ["rice", "egg", "vegetables"]
            for i in range(count):
                meals.append(MealSuggestion(
                    title=f"Simple Pantry Meal {i+1}",
                    ingredients=available_ingredients[:3],
                    calories=goal.calories,
                    protein=goal.protein or 20,
                    carbs=goal.carbs or 45,
                    fats=goal.fats or 15,
                    steps=[
                        "Note: OpenAI API key not configured. This is a basic suggestion.",
                        f"Combine {', '.join(available_ingredients[:2])} in a pan.",
                        "Cook on medium heat for 10-15 minutes.",
                        "Season to taste and serve hot."
                    ]
                ))
            return meals
        
        # Create OpenAI client and call API
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional chef and nutritionist. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.8  # Higher temperature for more variety
        )
        
        # Parse the AI response
        ai_response = response.choices[0].message.content.strip()
        meal_data = json.loads(ai_response)
        
        # Convert to MealSuggestion objects
        for meal in meal_data.get("meals", []):
            meals.append(MealSuggestion(
                title=meal.get("title", "AI-Generated Meal"),
                ingredients=meal.get("ingredients", []),
                calories=meal.get("calories", goal.calories),
                protein=meal.get("protein", goal.protein or 0),
                carbs=meal.get("carbs", goal.carbs or 0),
                fats=meal.get("fats", goal.fats or 0),
                steps=meal.get("steps", [])
            ))
        
        return meals
        
    except Exception as e:
        # Fallback multiple meal suggestions if AI fails
        available_ingredients = [item.name for item in pantry_items[:4]] if pantry_items else ["rice", "egg", "vegetables"]
        for i in range(count):
            meals.append(MealSuggestion(
                title=f"Simple Pantry Meal {i+1}",
                ingredients=available_ingredients[:3],
                calories=goal.calories,
                protein=goal.protein or 20,
                carbs=goal.carbs or 45,
                fats=goal.fats or 15,
                steps=[
                    f"AI generation failed ({str(e)}). Here's a basic suggestion:",
                    f"Combine {', '.join(available_ingredients[:2])} in a large pan.",
                    "Cook on medium heat, stirring occasionally.",
                    "Add seasonings and cook until ingredients are tender.",
                    "Serve hot and enjoy your meal!"
                ]
            ))
        return meals

@app.post("/meal/generate", response_model=MultipleMealSuggestions)
def generate_meal(goal: CalorieGoal):
    # Get current pantry contents
    current_pantry = pantry
    
    # Generate multiple AI-powered meal suggestions
    meals = generate_multiple_ai_meals(current_pantry, goal, count=3)
    return MultipleMealSuggestions(meals=meals)
