# app/routers/trip_summary.py
from fastapi import APIRouter, HTTPException, Request
from openai import OpenAI
import os

router = APIRouter(prefix="/trip-summary", tags=["trip-summary"])

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing.")
    return OpenAI(api_key=api_key)


@router.post("/")
async def generate_trip_summary(payload: dict):
    description = payload.get("description") if payload else None

    if not description or description.strip() == "":
        raise HTTPException(status_code=400, detail="Trip description is missing.")

    if len(description) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Description too long (max 1000 characters)."
        )

    try:
        client = get_openai_client()
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

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GenAI error: {str(e)}")
