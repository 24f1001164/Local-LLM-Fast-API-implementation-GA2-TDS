from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

app = FastAPI()


class InvoiceRequest(BaseModel):
    text: str


class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


@app.post("/extract", response_model=InvoiceResponse)
def extract(req: InvoiceRequest):

    prompt = f"""
Extract invoice information.

Return ONLY JSON.

{{
"vendor":"",
"amount":0,
"currency":"",
"date":"YYYY-MM-DD"
}}

Invoice:
{req.text}
"""

    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    import json

    data = json.loads(response.choices[0].message.content)

    data["currency"] = data["currency"].upper()

    return data
