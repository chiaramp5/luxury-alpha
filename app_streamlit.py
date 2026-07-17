import csv
import streamlit as st
import pandas as pd
from rapidfuzz import process

KNOWN_MODELS = ["Mini Kelly", "Kelly", "Birkin", "Constance", "Picotin"]
KNOWN_COLORS = ["Sakura", "Gold", "Noir", "Etoupe", "Rose", "Pink", "Mauve Sylvestre", "Bleu Brume"]
KNOWN_LEATHERS = ["Epsom", "Togo", "Clemence", "Swift", "Chevre", "Alligator", "Crocodile", "Ostrich", "Lizard"]
KNOWN_CONDITIONS = ["New", "Excellent", "Very Good", "Good", "Used"]
KNOWN_HARDWARE = ["Gold", "Palladium", "Rose Gold"]
KNOWN_SIZES = [18, 20, 25, 28, 30, 35, 40]
EXOTIC_LEATHERS = ["Alligator", "Crocodile", "Ostrich", "Lizard"]
COLORS = {

"Sakura": {
    "premium":15,
    "rarity":95,
    "collector":100,
    "liquidity":95
},

"Etoupe":{
    "premium":6,
    "rarity":75,
    "collector":82,
    "liquidity":96
},

"Noir":{
    "premium":3,
    "rarity":55,
    "collector":60,
    "liquidity":100
}

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


def find_from_list(description, items):

    description = description.lower()

    # Exact match
    for item in items:
        if item.lower() in description:
            return item

    # Fuzzy match on the whole description
    match = process.extractOne(
        description,
        items,
        processor=lambda x: x.lower(),
        score_cutoff=70
    )

    if match:
        return match[0]

    # Fuzzy match on each word
    words = description.split()

    best_item = None
    best_score = 0

    for word in words:
        match = process.extractOne(
            word,
            items,
            processor=lambda x: x.lower()
        )

        if match and match[1] > best_score:
            best_item = match[0]
            best_score = match[1]

    if best_score >= 70:
        return best_item

    return None


def clean_number(word):
    return word.replace(",", "").replace("€", "").replace("eur", "").replace("EUR", "").replace(".", "")


def find_price(description):
    for word in description.split():
        clean = clean_number(word).lower()
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
        if clean.isdigit() and int(clean) in KNOWN_SIZES:
            return int(clean)
    return None

ABBREVIATIONS = {
    "ghw": "Gold",
    "phw": "Palladium",
    "rghw": "Rose Gold",
    "mk20": "Mini Kelly 20",
    "mk": "Mini Kelly",
    "bk25": "Birkin 25",
    "bk": "Birkin",
    "k25": "Kelly 25",
}
def parse_bag_description(description):

    text = description.lower()

    for short, full in ABBREVIATIONS.items():
        text = text.replace(short, full.lower())

    return {
        "model": find_from_list(text, KNOWN_MODELS),
        "size": find_size(text),
        "color": find_from_list(text, KNOWN_COLORS),
        "leather": find_from_list(text, KNOWN_LEATHERS),
        "hardware": find_from_list(text, KNOWN_HARDWARE),
        "year": find_year(text),
        "condition": find_from_list(text, KNOWN_CONDITIONS),
        "price": find_price(text),
        "description": description,
    }


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
    # Never compare standard and exotic leathers
    if (
        bag["leather"] is not None
        and leather_category(bag["leather"]) != leather_category(comparable["leather"])
    ):
        return 0

    score = 0

    # Model (most important)
    if bag["model"] == comparable["model"]:
        score += 35

    # Size
    if bag["size"] == comparable["size"]:
        score += 20

    # Leather
    if bag["leather"] == comparable["leather"]:
        score += 15

    # Hardware
    if bag["hardware"] == comparable["hardware"]:
        score += 10

    # Condition
    if bag["condition"] == comparable["condition"]:
        score += 10

    # Year (close years still receive points)
    if bag["year"] is not None:
        difference = abs(bag["year"] - comparable["year"])
        score += max(0, 10 - difference * 2)

    return score


def find_top_comparables(bag, comparables):

    scored = []

    for comparable in comparables:
        similarity = calculate_similarity(bag, comparable)

        if similarity > 0:
            scored.append({
                "bag": comparable,
                "similarity": similarity
            })

    scored.sort(key=lambda x: x["similarity"], reverse=True)

    if len(scored) >= 5:
        return scored[:5]

    # Fallback: always return the 5 closest bags
    backup = []

    for comparable in comparables:
        backup.append({
            "bag": comparable,
            "similarity": calculate_similarity(bag, comparable)
        })

    backup.sort(key=lambda x: x["similarity"], reverse=True)

    return backup[:5]

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


def get_recommendation(score):
    if score >= 85:
        return "BUY"
    elif score >= 65:
        return "NEGOTIATE"
    else:
        return "PASS"


def run_valuation(bag):
    comparables = load_comparables()
    top_comparables = find_top_comparables(bag, comparables)

    if len(top_comparables) == 0 or bag["price"] is None:
        st.error("Not enough relevant comparables to complete valuation.")
        return

    fair_value = estimate_fair_value(top_comparables)
    fair_value = apply_color_premium(fair_value, bag)
    asking_price = bag["price"]
    discount = (fair_value - asking_price) / fair_value * 100
    upside = fair_value - asking_price

    rarity_score = calculate_rarity_score(bag)
    liquidity_score = calculate_liquidity_score(bag)
    investment_score = calculate_investment_score(discount, rarity_score, liquidity_score)
    recommendation = get_recommendation(investment_score)

    st.markdown("---")
    st.markdown("## Valuation Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Fair Value", euro(fair_value))
    col2.metric("Market Price", euro(asking_price))
    col3.metric("Potential Return", euro(upside))

    st.metric(
    "Valuation Confidence",
    f"{round(sum(c['similarity'] for c in top_comparables)/len(top_comparables))}%"
)

    st.markdown("## Investment Opinion")

    if recommendation == "BUY":
        st.success("BUY — Attractive relative to comparable sales")
    elif recommendation == "NEGOTIATE":
        st.warning("NEGOTIATE — Fairly priced, but there may be room to improve entry price")
    else:
        st.error("PASS — Price appears above current comparable value")

    st.metric("Investment Score", str(investment_score) + "/100")
    st.metric("Market Discount", str(round(discount, 1)) + "%")

    st.markdown("---")
    st.markdown("## Bag Profile")

    details = pd.DataFrame({
        "Attribute": ["Model", "Size", "Color", "Leather", "Leather Category", "Hardware", "Year", "Condition"],
        "Value": [
            bag["model"], bag["size"], bag["color"], bag["leather"],
            leather_category(bag["leather"]) if bag["leather"] else None,
            bag["hardware"], bag["year"], bag["condition"]
        ]
    })
    st.table(details)

    st.markdown("---")
    st.markdown("## Market Indicators")

    st.write("Investment Potential")
    st.progress(investment_score / 100)

    st.write("Liquidity")
    st.progress(liquidity_score / 100)

    st.write("Rarity")
    st.progress(rarity_score / 100)

    st.markdown("---")
    st.markdown("## Price Positioning")

    price_chart = pd.DataFrame(
        {"Price": [asking_price, fair_value]},
        index=["Asking Price", "Fair Value"]
    )
    st.bar_chart(price_chart)

    st.markdown("---")
    st.markdown("## Comparable Sales")

    comps = []
    for item in top_comparables:
        comp = item["bag"]
        comps.append({
            "Comparable": f"{comp['model']} {comp['size']} {comp['leather']} {comp['hardware']}",
            "Year": comp["year"],
            "Condition": comp["condition"],
            "Price": euro(comp["price"]),
            "Similarity": str(item["similarity"]) + "/100"
        })

    st.table(pd.DataFrame(comps))

    st.markdown("---")
    st.markdown("## Market Commentary")

    commentary = f"""
Based on the available comparable sales, this listing appears attractively priced.

The asking price of **{euro(asking_price)}** is approximately **{round(discount, 1)}% below**
the estimated fair value of **{euro(fair_value)}**.

Comparable selection separates standard and exotic leathers, reducing the risk of comparing
bags from fundamentally different resale markets.

The current investment score is **{investment_score}/100**.
"""

    st.write(commentary)


st.set_page_config(page_title="Luxury Alpha", page_icon="👜", layout="centered")

st.title("Luxury Alpha")

st.caption(
    "Professional valuation engine for Hermès handbags • Comparable sales • Fair value estimation"
)

st.markdown("## Guided Valuation Form")

col1, col2 = st.columns(2)

with col1:
    model = st.selectbox("Model", KNOWN_MODELS)
    size = st.selectbox("Size", KNOWN_SIZES)
    color = st.selectbox("Color", KNOWN_COLORS)
    leather = st.selectbox("Leather", KNOWN_LEATHERS)

with col2:
    hardware = st.selectbox("Hardware", KNOWN_HARDWARE)
    year = st.number_input("Year", min_value=1980, max_value=2035, value=2023)
    condition = st.selectbox("Condition", KNOWN_CONDITIONS)
    price = st.number_input("Asking Price (€)", min_value=0, value=20000, step=500)

if st.button("Generate Report", use_container_width=True):
    bag = {
        "model": model,
        "size": size,
        "color": color,
        "leather": leather,
        "hardware": hardware,
        "year": year,
        "condition": condition,
        "price": price,
        "description": f"{model} {size} {color} {leather} {hardware} {year} {condition} {price}"
    }

    run_valuation(bag)