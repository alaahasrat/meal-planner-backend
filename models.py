from pydantic import BaseModel
from typing import Optional, List

class PantryItem(BaseModel):
    name: str
    quantity: float
    unit: str
    # Comprehensive nutritional information per serving/reference amount
    calories: Optional[float] = None          # kcal
    protein: Optional[float] = None           # g
    carbohydrates: Optional[float] = None     # g
    sugars: Optional[float] = None            # g (of which sugars)
    fats: Optional[float] = None              # g
    saturated_fat: Optional[float] = None     # g (of which saturated fat)
    fiber: Optional[float] = None             # g
    sodium: Optional[float] = None            # mg
    serving_size: Optional[float] = None      # serving size amount
    serving_unit: Optional[str] = "g"         # serving size unit (g, kg, ml, etc.)

class CalorieGoal(BaseModel):
    calories: float
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fats: Optional[float] = None

class MealSuggestion(BaseModel):
    title: str
    ingredients: List[str]
    calories: float
    protein: float
    carbs: float
    fats: float
    steps: List[str]

class MultipleMealSuggestions(BaseModel):
    meals: List[MealSuggestion]
