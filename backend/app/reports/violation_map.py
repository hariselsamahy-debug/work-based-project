"""Violation type -> human description, the OSHA standards that usually apply, and a search query
for the OSHA text index. The LLM may cite other sections if the retrieved text supports it."""

VIOLATIONS: dict[str, dict] = {
    "NO_HARDHAT": {
        "title": "Worker without head protection (hard hat)",
        "standards": ["29 CFR 1910.135"],
        "query": "head protection protective helmets falling objects 1910.135",
    },
    "NO_VEST": {
        "title": "Worker without high-visibility safety vest",
        "standards": ["29 CFR 1910.132"],
        "query": "personal protective equipment hazard assessment high visibility 1910.132",
    },
    "NO_MASK": {
        "title": "Worker without respiratory / face protection",
        "standards": ["29 CFR 1910.134"],
        "query": "respiratory protection respirator 1910.134",
    },
    "NO_GLOVES": {
        "title": "Worker without hand protection (gloves)",
        "standards": ["29 CFR 1910.138"],
        "query": "hand protection gloves 1910.138",
    },
    "NO_BOOTS": {
        "title": "Worker without protective footwear",
        "standards": ["29 CFR 1910.136"],
        "query": "foot protection protective footwear 1910.136",
    },
    "FIRE": {
        "title": "Fire detected",
        "standards": ["29 CFR 1910.38", "29 CFR 1910.39", "29 CFR 1910.157"],
        "query": "emergency action plan fire prevention plan portable fire extinguishers 1910.38 1910.157",
    },
    "SMOKE": {
        "title": "Smoke detected",
        "standards": ["29 CFR 1910.38", "29 CFR 1910.39"],
        "query": "emergency action plan fire prevention plan alarm 1910.38 1910.39",
    },
    "FALL": {
        "title": "Worker fall detected",
        "standards": ["29 CFR 1910.22", "29 CFR 1910.151"],
        "query": "walking-working surfaces slip trip fall medical services first aid 1910.22 1910.151",
    },
}


def describe(violation_type: str) -> dict:
    return VIOLATIONS.get(violation_type, {
        "title": violation_type.replace("_", " ").title(),
        "standards": [],
        "query": violation_type.replace("_", " ").lower(),
    })
