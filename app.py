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

# Try common invoice labels first
amount_patterns = [
    r"Total\s*Due[:\s\$€£]*([0-9]+(?:\.[0-9]{1,2})?)",
    r"Amount\s*Due[:\s\$€£]*([0-9]+(?:\.[0-9]{1,2})?)",
    r"Balance\s*Due[:\s\$€£]*([0-9]+(?:\.[0-9]{1,2})?)",
    r"Grand\s*Total[:\s\$€£]*([0-9]+(?:\.[0-9]{1,2})?)",
    r"Invoice\s*Total[:\s\$€£]*([0-9]+(?:\.[0-9]{1,2})?)",
    r"Total[:\s\$€£]*([0-9]+(?:\.[0-9]{1,2})?)",
]

for p in amount_patterns:
    m = re.search(p, text, re.IGNORECASE)
    if m:
        amount = float(m.group(1))
        break

# Fallback: use the largest monetary-looking number
if amount == 0.0:
    numbers = re.findall(r"\b\d+(?:\.\d{1,2})?\b", text)

    candidates = []

    for n in numbers:
        value = float(n)

        # Ignore year and small numbers that are likely dates
        if value != 2026 and value >= 50:
            candidates.append(value)

    if candidates:
        amount = max(candidates)
