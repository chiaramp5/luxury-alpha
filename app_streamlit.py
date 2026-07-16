import csv
import streamlit as st
import pandas as pd


KNOWN_MODELS = ["Mini Kelly", "Kelly", "Birkin", "Constance", "Picotin"]
KNOWN_COLORS = ["Sakura", "Gold", "Noir", "Etoupe", "Rose", "Pink", "Mauve Sylvestre", "Bleu Brume"]
KNOWN_LEATHERS = ["Epsom", "Togo", "Clemence", "Swift", "Chevre", "Alligator", "Crocodile", "Ostrich", "Lizard"]
KNOWN_CONDITIONS = ["New", "Excellent", "Very Good", "Good", "Used"]
KNOWN_HARDWARE = ["Gold", "Palladium", "Rose Gold"]
KNOWN_SIZES = ["18", "20", "25", "28", "30", "35", "40"]

EXOTIC_LEATHERS = ["Alligator", "Crocodile", "Ostrich", "Lizard"]
RARE_KEYWORDS = ["limited edition", "blue box", "special order", "hss", "rare", "sakura"]


def euro(value):
    return "€" + format(round(value), ",")


def find_from_list(description, items):
    for item in items:
        if item.lower() in description.lower():
            return item
    return None


def clean_number(word):
    return word.replace(",", "").replace("€", "").replace("eur", "").replace("EUR", "")


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
        if clean in KNOWN_SIZES:
            return int(clean)
    return None


def parse_bag_description(description):
    return {
        "model": find_from_list(description, KNOWN_MODELS),
        "size": find_size(description),
        "color": find_from_list(description, KNOWN_COLORS),
        "leather": find_from_list(description, KNOWN_LEATHERS),
        "hardware": find_from_list(description, KNOWN_HARDWARE),
        "year": find_year(description),
        "condition": find_from_list(description, KNOWN_CONDITIONS),
        "price": find_price(description),
        "description": description
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
            results.append({"bag": comparable, "similarity": similarity})
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

    return round(discount_score * 0.50 + rarity_score * 0.25 + liquidity_score * 0.25)


def get_recommendation(score):
    if score >= 85:
        return "BUY"
    elif score >= 65:
        return "NEGOTIATE"
    else:
        return "PASS"


st.set_page_config(page_title="Luxury Alpha", page_icon="👜", layout="centered")

st.markdown("# Luxury Alpha")
st.markdown("### Hermès Resale Market Valuation")
st.caption("Comparable sales · market discount · investment scoring")

description = st.text_area(
    "Paste listing",
    height=150,
    placeholder="Mini Kelly 20 Sakura Epsom Gold 2023 Excellent €20,000"
)

if st.button("Generate Report", use_container_width=True):
    if not description:
        st.warning("Please paste a listing first.")
    else:
        bag = parse_bag_description(description)
        comparables = load_comparables()
        top_comparables = find_top_comparables(bag, comparables)

        if len(top_comparables) == 0 or bag["price"] is None:
            st.error("More listing details are required to complete the valuation.")
        else:
            fair_value = estimate_fair_value(top_comparables)
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
            col2.metric("Asking Price", euro(asking_price))
            col3.metric("Potential Upside", euro(upside))

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
            st.markdown("## Bag Characteristics")

            details = pd.DataFrame({
                "Attribute": ["Model", "Size", "Color", "Leather", "Hardware", "Year", "Condition"],
                "Value": [
                    bag["model"],
                    bag["size"],
                    bag["color"],
                    bag["leather"],
                    bag["hardware"],
                    bag["year"],
                    bag["condition"],
                ]
            })

            st.table(details)

            st.markdown("---")
            st.markdown("## Investment Dashboard")

            st.write("Investment Potential")
            st.progress(investment_score / 100)
            st.write(str(investment_score) + "/100")

            st.write("Liquidity")
            st.progress(liquidity_score / 100)
            st.write(str(liquidity_score) + "/100")

            st.write("Rarity")
            st.progress(rarity_score / 100)
            st.write(str(rarity_score) + "/100")

            st.markdown("---")
            st.markdown("## Fair Value vs Asking Price")

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

The asking price of **{euro(asking_price)}** is approximately **{round(discount,1)}% below** the estimated fair value of **{euro(fair_value)}**.

Comparable transactions support the valuation, resulting in an Investment Score of **{investment_score}/100**.

Overall, current market evidence suggests that this listing represents an attractive buying opportunity.
"""

            st.write(commentary)

            st.caption(
                "Methodology: Fair value is estimated using comparable resale transactions selected by the Luxury Alpha Similarity Model."
            )
            