import csv
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "bags.csv"

KNOWN_MODELS = ["Mini Kelly", "Kelly", "Birkin", "Constance", "Picotin"]
KNOWN_COLORS = ["Sakura", "Gold", "Noir", "Etoupe", "Rose", "Pink", "Mauve Sylvestre", "Bleu Brume"]
KNOWN_LEATHERS = ["Epsom", "Togo", "Clemence", "Swift", "Chevre", "Alligator", "Crocodile", "Ostrich", "Lizard"]
KNOWN_CONDITIONS = ["New", "Excellent", "Very Good", "Good", "Used"]
KNOWN_HARDWARE = ["Gold", "Palladium", "Rose Gold"]
KNOWN_SIZES = [18, 20, 22, 24, 25, 28, 30, 35, 40]
EXOTIC_LEATHERS = ["Alligator", "Crocodile", "Ostrich", "Lizard"]

COLORS = {
    "Sakura": {"premium": 15, "rarity": 95, "collector": 100, "liquidity": 95},
    "Etoupe": {"premium": 6, "rarity": 75, "collector": 82, "liquidity": 96},
    "Noir": {"premium": 3, "rarity": 55, "collector": 60, "liquidity": 100},
    "Gold": {"premium": 4, "rarity": 60, "collector": 65, "liquidity": 98},
    "Rose": {"premium": 8, "rarity": 70, "collector": 75, "liquidity": 85},
    "Pink": {"premium": 8, "rarity": 70, "collector": 75, "liquidity": 85},
    "Mauve Sylvestre": {"premium": 12, "rarity": 88, "collector": 90, "liquidity": 70},
    "Bleu Brume": {"premium": 10, "rarity": 85, "collector": 88, "liquidity": 72},
}


def apply_color_premium(fair_value, bag):
    color = bag.get("color")
    if color in COLORS:
        premium = COLORS[color]["premium"]
        return fair_value * (1 + premium / 100)
    return fair_value


def euro(value):
    return "€" + format(round(value), ",")


def leather_category(leather):
    if leather in EXOTIC_LEATHERS:
        return "Exotic"
    return "Standard"


def load_comparables():
    comparables = []
    with open(DATA_PATH, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            comparables.append({
                "model": row["model"],
                "size": int(row["size"]),
                "color": row["color"],
                "leather": row["leather"],
                "hardware": row["hardware"],
                "year": int(row["year"]),
                "condition": row["condition"],
                "price": int(row["price"]),
            })
    return comparables


def calculate_similarity(bag, comparable):
    # Never compare standard and exotic leathers
    if (
        bag["leather"] is not None
        and leather_category(bag["leather"]) != leather_category(comparable["leather"])
    ):
        return 0

    score = 0

    if bag["model"] == comparable["model"]:
        score += 35
    if bag["size"] == comparable["size"]:
        score += 20
    if bag["leather"] == comparable["leather"]:
        score += 15
    if bag["hardware"] == comparable["hardware"]:
        score += 10
    if bag["condition"] == comparable["condition"]:
        score += 10
    if bag["year"] is not None:
        difference = abs(bag["year"] - comparable["year"])
        score += max(0, 10 - difference * 2)

    return score


def find_top_comparables(bag, comparables):
    same_model_comparables = [
        comparable for comparable in comparables if comparable["model"] == bag["model"]
    ]

    scored = []
    for comparable in same_model_comparables:
        similarity = calculate_similarity(bag, comparable)
        if similarity > 0:
            scored.append({"bag": comparable, "similarity": similarity})

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:5]


def estimate_fair_value(top_comparables):
    prices = [item["bag"]["price"] for item in top_comparables]
    return sum(prices) / len(prices)


def calculate_rarity_score(bag):
    score = 40
    if bag["leather"] in EXOTIC_LEATHERS:
        score += 30
    if bag["model"] == "Mini Kelly":
        score += 15
    if bag["color"] in ["Sakura", "Mauve Sylvestre", "Bleu Brume"]:
        score += 15
    return min(score, 100)


def calculate_liquidity_score(bag):
    score = 50
    if bag["model"] in ["Mini Kelly", "Birkin", "Kelly"]:
        score += 20
    if bag["size"] in [20, 25]:
        score += 15
    if bag["condition"] in ["New", "Excellent"]:
        score += 15
    return min(score, 100)


def calculate_investment_score(discount, rarity_score, liquidity_score):
    if discount >= 15:
        discount_score = 100
    elif discount >= 10:
        discount_score = 90
    elif discount > 0:
        discount_score = 70
    else:
        discount_score = 35

    return round(discount_score * 0.50 + rarity_score * 0.25 + liquidity_score * 0.25)


def get_recommendation(discount):
    if discount >= 15:
        return "BUY"
    elif discount >= 0:
        return "NEGOTIATE"
    else:
        return "PASS"


def run_valuation(bag):
    comparables = load_comparables()
    top_comparables = find_top_comparables(bag, comparables)

    if len(top_comparables) == 0 or bag["price"] is None:
        return {"error": "Not enough relevant comparables to complete valuation."}

    fair_value = estimate_fair_value(top_comparables)
    fair_value = apply_color_premium(fair_value, bag)
    asking_price = bag["price"]
    discount = (fair_value - asking_price) / fair_value * 100
    upside = fair_value - asking_price

    rarity_score = calculate_rarity_score(bag)
    liquidity_score = calculate_liquidity_score(bag)
    investment_score = calculate_investment_score(discount, rarity_score, liquidity_score)
    recommendation = get_recommendation(discount)
    confidence = round(sum(c["similarity"] for c in top_comparables) / len(top_comparables))

    if recommendation == "BUY":
        intro = "this listing appears attractively priced"
    elif recommendation == "NEGOTIATE":
        intro = "this listing appears broadly aligned with comparable market values"
    else:
        intro = "this listing appears priced above comparable market values"

    commentary = (
        f"Based on the available comparable sales, {intro}. "
        f"The asking price of {euro(asking_price)} is approximately "
        f"{abs(round(discount, 1))}% {'below' if discount >= 0 else 'above'} "
        f"the estimated fair value of {euro(fair_value)}. "
        f"The current investment score is {investment_score}/100."
    )

    comparables_out = []
    for item in top_comparables:
        comp = item["bag"]
        comparables_out.append({
            "label": f"{comp['model']} {comp['size']} {comp['leather']} {comp['hardware']}",
            "year": comp["year"],
            "condition": comp["condition"],
            "price": comp["price"],
            "price_formatted": euro(comp["price"]),
            "similarity": item["similarity"],
        })

    return {
        "fair_value": round(fair_value),
        "fair_value_formatted": euro(fair_value),
        "asking_price": asking_price,
        "asking_price_formatted": euro(asking_price),
        "upside": round(upside),
        "upside_formatted": euro(upside),
        "confidence": confidence,
        "recommendation": recommendation,
        "investment_score": investment_score,
        "discount": round(discount, 1),
        "rarity_score": rarity_score,
        "liquidity_score": liquidity_score,
        "characteristics": {
            "model": bag["model"],
            "size": bag["size"],
            "color": bag["color"],
            "leather": bag["leather"],
            "leather_category": leather_category(bag["leather"]) if bag["leather"] else None,
            "hardware": bag["hardware"],
            "year": bag["year"],
            "condition": bag["condition"],
        },
        "comparables": comparables_out,
        "commentary": commentary,
    }
