from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InvoiceRequest(BaseModel):
    text: str

class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


@app.post("/extract", response_model=InvoiceResponse)
def extract(req: InvoiceRequest):

    text = req.text.strip()

    if not text:
        return InvoiceResponse(
            vendor="",
            amount=0.0,
            currency="USD",
            date="1970-01-01"
        )

    # -----------------------
    # Vendor
    # -----------------------
    vendor = ""

    patterns = [
        r"Vendor[:\s]+(.+)",
        r"Supplier[:\s]+(.+)",
        r"Bill From[:\s]+(.+)",
        r"From[:\s]+(.+)"
    ]

    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            vendor = m.group(1).split("\n")[0].strip()
            break

    # -----------------------
    # Currency
    # -----------------------
    currency = "USD"

    m = re.search(r"\b(USD|EUR|GBP)\b", text, re.IGNORECASE)

    if m:
        currency = m.group(1).upper()

    # -----------------------
    # Date
    # -----------------------
    date = ""

    m = re.search(r"(2026-\d{2}-\d{2})", text)

    if m:
        date = m.group(1)

    # -----------------------
    # Amount
    # -----------------------
    amount = 0.0

    amount_patterns = [
        r"Total Due[:\s]*([0-9]+(?:\.[0-9]+)?)",
        r"Amount Due[:\s]*([0-9]+(?:\.[0-9]+)?)",
        r"Total[:\s]*([0-9]+(?:\.[0-9]+)?)",
        r"([0-9]+(?:\.[0-9]+)?)\s*(USD|EUR|GBP)"
    ]

    for p in amount_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            amount = float(m.group(1))
            break

    return InvoiceResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=date
    )
