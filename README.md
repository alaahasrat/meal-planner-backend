# Calorie & Pantry-Based Meal Generator Backend

This is the backend for the Calorie & Pantry-Based Meal Generator app. It provides API endpoints for managing pantry items and calorie goals.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

## Endpoints

- `GET /pantry` — List all pantry items
- `POST /pantry` — Add a pantry item
- `DELETE /pantry/{item_name}` — Remove a pantry item

More endpoints coming soon for calorie goals and meal generation.
