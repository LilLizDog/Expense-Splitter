# app/routers/trip_summary.py
from fastapi import APIRouter, HTTPException
from openai import OpenAI
import os

router = APIRouter(prefix="/trip-summary", tags=["trip-summary"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/")
async def generate_trip_summary(description: str | None):
    if not description or description.strip() == "":
        raise HTTPException(status_code=400, detail="Trip description is missing.")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Write a short, friendly trip summary."},
                {"role": "user", "content": description},
            ],
            max_tokens=200
        )

        summary = response.choices[0].message.content
        return {"summary": summary}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GenAI error: {str(e)}")
