"""Generates a large, realistic-but-synthetic comparable-sales dataset for
Luxury Alpha, replacing the original ~100-row bags.csv with ~700 rows that
span far more model/size/leather/color/hardware/year/condition combinations.

Not scraped from any real marketplace — prices are derived from a simple
pricing model (base price per model/size, leather/hardware/condition/year/
color multipliers, plus bounded random noise) calibrated to sit in plausible
real-world Hermès resale ranges. Run this script whenever the pricing model
or coverage needs to change; the output is committed so the app stays fast
and deterministic at runtime.
"""
import csv
import random
from pathlib import Path

from valuation import COLORS, KNOWN_HARDWARE

OUTPUT_PATH = Path(__file__).parent / "data" / "bags.csv"

STANDARD_LEATHERS = ["Epsom", "Togo", "Clemence", "Swift", "Chevre"]
EXOTIC_LEATHERS = ["Alligator", "Crocodile", "Ostrich", "Lizard"]
CONDITIONS = ["New", "Excellent", "Very Good", "Good", "Used"]
YEARS = list(range(2017, 2026))

# Base price (EUR) for standard leather / Palladium hardware / Excellent
# condition / ~2023, per (model, size).
MODEL_SIZES = {
    "Mini Kelly": {20: 21500},
    "Kelly": {25: 15500, 28: 16500},
    "Birkin": {25: 19500, 30: 17500, 35: 15500},
    "Constance": {18: 9800, 24: 12500},
    "Picotin": {18: 4200, 22: 4800},
}

# Exotic leathers aren't realistically produced for every model/size — only
# allow them where Hermès actually offers them.
EXOTIC_ALLOWED = {"Mini Kelly", "Kelly", "Birkin", "Constance"}

LEATHER_MULTIPLIER = {
    "Togo": 1.00, "Clemence": 0.98, "Epsom": 1.03, "Swift": 1.08, "Chevre": 1.12,
    "Alligator": 4.6, "Crocodile": 5.1, "Ostrich": 3.3, "Lizard": 3.9,
}
HARDWARE_MULTIPLIER = {"Palladium": 1.00, "Gold": 1.02, "Rose Gold": 1.06}
CONDITION_MULTIPLIER = {
    "New": 1.12, "Excellent": 1.00, "Very Good": 0.90, "Good": 0.78, "Used": 0.65,
}

ROWS_PER_MODEL = {
    "Birkin": 200,
    "Kelly": 150,
    "Mini Kelly": 100,
    "Constance": 120,
    "Picotin": 130,
}

ALL_COLORS = list(COLORS.keys())


def pick_leather(model):
    if model in EXOTIC_ALLOWED and random.random() < 0.15:
        return random.choice(EXOTIC_LEATHERS)
    return random.choice(STANDARD_LEATHERS)


def price_for(model, size, leather, hardware, year, condition, color):
    base = MODEL_SIZES[model][size]
    price = base * LEATHER_MULTIPLIER[leather] * HARDWARE_MULTIPLIER[hardware]
    price *= CONDITION_MULTIPLIER[condition]
    price *= 1 + (year - 2023) * 0.015
    if color in COLORS:
        price *= 1 + (COLORS[color]["premium"] / 100) * 0.5
    price *= random.uniform(0.95, 1.05)
    return int(round(price / 50) * 50)


def generate_rows():
    rows = []
    for model, count in ROWS_PER_MODEL.items():
        sizes = list(MODEL_SIZES[model].keys())
        for _ in range(count):
            size = random.choice(sizes)
            leather = pick_leather(model)
            hardware = random.choice(KNOWN_HARDWARE)
            year = random.choice(YEARS)
            condition = random.choice(CONDITIONS)
            color = random.choice(ALL_COLORS)
            price = price_for(model, size, leather, hardware, year, condition, color)
            rows.append({
                "model": model,
                "size": size,
                "color": color,
                "leather": leather,
                "hardware": hardware,
                "year": year,
                "condition": condition,
                "price": price,
            })
    return rows


def main():
    random.seed(42)
    rows = generate_rows()
    rows.sort(key=lambda r: (r["model"], r["size"], r["price"]))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["model", "size", "color", "leather", "hardware", "year", "condition", "price"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
