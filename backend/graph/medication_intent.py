"""Detect user messages that ask for drugs / treatment recommendations."""

MEDICATION_ADVICE_MARKERS = (
    "give me medicine",
    "give me medication",
    "give me meds",
    "what medicine",
    "what medication",
    "what drug",
    "what pills",
    "which medicine",
    "which medication",
    "which drug",
    "prescription",
    "prescribe",
    "medication for",
    "medicine for",
    "meds for",
    "drug for",
    "pill for",
    "pills for",
    "antibiotic",
    "antibiotics",
    "dosage",
    "dose of",
    "how much should i take",
    "should i take",
    "recommend a drug",
    "recommend medicine",
    "otc for",
    "over the counter",
    "what can i take",
    "something for the pain",
    "painkiller",
    "pain killer",
)


def wants_medication_advice(text: str) -> bool:
    if not isinstance(text, str) or not text.strip():
        return False
    lowered = text.lower()
    return any(marker in lowered for marker in MEDICATION_ADVICE_MARKERS)
