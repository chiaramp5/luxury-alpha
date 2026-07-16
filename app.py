import csv
import json
from ai import ask_ai

KNOWN_MODELS = ["Mini Kelly", "Kelly", "Birkin", "Constance", "Picotin"]
KNOWN_LEATHERS = ["Epsom", "Togo", "Clemence", "Swift", "Chevre", "Alligator", "Crocodile", "Ostrich", "Lizard"]
KNOWN_CONDITIONS = ["New", "Excellent", "Very Good", "Good", "Used"]
KNOWN_HARDWARE = ["Gold", "Palladium", "Rose Gold"]
KNOWN_SIZES = ["18", "20", "25", "28", "30", "35", "40"]

EXOTIC_LEATHERS = ["Alligator", "Crocodile", "Ostrich", "Lizard"]
RARE_KEYWORDS = ["limited edition", "blue box", "special order", "hss", "rare", "sakura"]


def find_from_list(description, items):
    for item in items:
        if item.lower() in description.lower():
            return item
    return None


def clean_number(word):
    return word.replace(",", "").replace("€", "").replace("eur", "").replace("EUR", "")


def find_price(description):
    for word in description.split():
        clean = clean_number(word)

        if clean.endswith("k") and clean[:-1].isdigit():
            return int(clean[:-1]) * 1000

        if clean.isdigit():
            number = int(clean)
            if number >= 3000:
                return number

    return None


def find_year(description):
    for word in description.split():
        clean = clean_number(word)

        if clean.isdigit():
            number = int(clean)
            if 1980 <= number <= 2035:
                return number

    return None


def find_size(description):
    for word in description.split():
        clean = clean_number(word)

        if clean in KNOWN_SIZES:
            return int(clean)

    return None


def parse_bag_description(description):
    return {
        "model": find_from_list(description, KNOWN_MODELS),
        "size": find_size(description),
        "color": None,
        "leather": find_from_list(description, KNOWN_LEATHERS),
        "hardware": find_from_list(description, KNOWN_HARDWARE),
        "year": find_year(description),
        "condition": find_from_list(description, KNOWN_CONDITIONS),
        "price": find_price(description),
        "description": description
    }


def calculate_parser_confidence(bag):
    score = 0

    if bag["model"]:
        score += 20
    if bag["size"]:
        score += 10
    if bag["leather"]:
        score += 15
    if bag["hardware"]:
        score += 10
    if bag["year"]:
        score += 15
    if bag["condition"]:
        score += 10
    if bag["price"]:
        score += 20

    return score


def complete_with_ai(bag):
    print("\nParser confidence low. Asking AI...")

    try:
        ai_text = ask_ai(bag["description"])
        ai_data = json.loads(ai_text)

        for key in ["model", "size", "color", "leather", "hardware", "year", "condition", "price"]:
            if bag.get(key) is None and ai_data.get(key) is not None:
                bag[key] = ai_data[key]

        print("AI completed missing fields.")

    except Exception as error:
        print("AI fallback failed:", error)

    return bag


def load_comparables():
    comparables = []

    with open("bags.csv", mode="r") as file:
        reader = csv.DictReader(file)

        for row in reader:
            comparables.append({
                "model": row["model"],
                "size": int(row["size"]),
                "leather": row["leather"],
                "hardware": row["hardware"],
                "year": int(row["year"]),
                "condition": row["condition"],
                "price": int(row["price"]),
            })

    return comparables


def calculate_similarity(bag, comparable):
    score = 0

    if bag["model"] == comparable["model"]:
        score += 40
    if bag["size"] == comparable["size"]:
        score += 20
    if bag["leather"] == comparable["leather"]:
        score += 15
    if bag["hardware"] == comparable["hardware"]:
        score += 10
    if bag["year"] == comparable["year"]:
        score += 10
    if bag["condition"] == comparable["condition"]:
        score += 5

    return score


def find_top_comparables(bag, comparables):
    results = []

    for comparable in comparables:
        similarity = calculate_similarity(bag, comparable)

        if similarity >= 70:
            results.append({
                "bag": comparable,
                "similarity": similarity
            })

    return sorted(results, key=lambda x: x["similarity"], reverse=True)[:5]


def estimate_fair_value(top_comparables):
    prices = [item["bag"]["price"] for item in top_comparables]
    return sum(prices) / len(prices)


def calculate_rarity_score(bag):
    score = 40
    description = bag["description"].lower()

    if bag["leather"] in EXOTIC_LEATHERS:
        score += 25
    if bag["model"] == "Mini Kelly":
        score += 15
    for keyword in RARE_KEYWORDS:
        if keyword in description:
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

    final_score = (
        discount_score * 0.50
        + rarity_score * 0.25
        + liquidity_score * 0.25
    )

    return round(final_score)


def get_recommendation(score):
    if score >= 85:
        return "BUY"
    elif score >= 65:
        return "NEGOTIATE"
    else:
        return "PASS"


description = input("Describe the bag: ")

bag = parse_bag_description(description)
confidence = calculate_parser_confidence(bag)

if confidence < 80:
    bag = complete_with_ai(bag)

comparables = load_comparables()
top_comparables = find_top_comparables(bag, comparables)

print("\nLuxury Alpha Investment Report")
print("--------------------------------")
print("Parsed Bag:", bag)

if len(top_comparables) == 0 or bag["price"] is None:
    print("\nNot enough information to complete valuation.")
else:
    fair_value = estimate_fair_value(top_comparables)
    asking_price = bag["price"]
    discount = (fair_value - asking_price) / fair_value * 100

    rarity_score = calculate_rarity_score(bag)
    liquidity_score = calculate_liquidity_score(bag)
    investment_score = calculate_investment_score(discount, rarity_score, liquidity_score)
    recommendation = get_recommendation(investment_score)

    print("\nTop Comparables:")
    for item in top_comparables:
        comp = item["bag"]
        print(
            comp["model"], comp["size"], comp["leather"], comp["hardware"],
            comp["year"], comp["condition"], "€" + str(comp["price"]),
            "| Similarity:", str(item["similarity"]) + "/100"
        )

    print("\nEstimated Fair Value: €" + str(round(fair_value)))
    print("Asking Price: €" + str(asking_price))
    print("Discount: " + str(round(discount, 1)) + "%")

    print("\nRarity Score:", str(rarity_score) + "/100")
    print("Liquidity Score:", str(liquidity_score) + "/100")
    print("Investment Score:", str(investment_score) + "/100")
    print("Recommendation:", recommendation)

    print("\nAnalysis:")
    print(
        "This bag appears " + recommendation.lower()
        + " because the asking price is "
        + str(round(discount, 1))
        + "% below estimated fair value, based on "
        + str(len(top_comparables))
        + " comparable sales."
    )