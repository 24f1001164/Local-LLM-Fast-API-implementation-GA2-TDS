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

    vendor_patterns = [
        r"Vendor[:\s]+(.+)",
        r"Supplier[:\s]+(.+)",
        r"Bill From[:\s]+(.+)",
        r"From[:\s]+(.+)"
    ]

    for pattern in vendor_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            vendor = match.group(1).split("\n")[0].strip()
            break

    # -----------------------
    # Currency
    # -----------------------
    currency = "USD"

    match = re.search(r"\b(USD|EUR|GBP)\b", text, re.IGNORECASE)
    if match:
        currency = match.group(1).upper()

    # -----------------------
    # Date
    # -----------------------
    date = ""

    match = re.search(r"(2026-\d{2}-\d{2})", text)
    if match:
        date = match.group(1)

    # -----------------------
    # Amount
    # -----------------------
    amount = 0.0

    amount_patterns = [
        r"Total\s*Due[:\s\$€£]*([0-9]+(?:\.[0-9]{1,2})?)",
        r"Amount\s*Due[:\s\$€£]*([0-9]+(?:\.[0-9]{1,2})?)",
        r"Balance\s*Due[:\s\$€£]*([0-9]+(?:\.[0-9]{1,2})?)",
        r"Grand\s*Total[:\s\$€£]*([0-9]+(?:\.[0-9]{1,2})?)",
        r"Invoice\s*Total[:\s\$€£]*([0-9]+(?:\.[0-9]{1,2})?)",
        r"Total[:\s\$€£]*([0-9]+(?:\.[0-9]{1,2})?)",
        r"([0-9]+(?:\.[0-9]{1,2})?)\s*(USD|EUR|GBP)"
    ]

    for pattern in amount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = float(match.group(1))
            break

    # Fallback: choose the largest monetary-looking number
    if amount == 0.0:
        numbers = re.findall(r"\b\d+(?:\.\d{1,2})?\b", text)

        candidates = []

        for n in numbers:
            value = float(n)

            # Ignore year values and small date/day values
            if value != 2026 and value >= 50:
                candidates.append(value)

        if candidates:
            amount = max(candidates)

    return InvoiceResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=date
    )
