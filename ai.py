from openai import OpenAI

client = OpenAI()


def generate_market_commentary(
    bag,
    fair_value,
    asking_price,
    investment_score,
    recommendation,
    top_comparables,
):

    prompt = f"""
You are a luxury investment analyst specializing in the Hermès resale market.

Write a concise professional market commentary.

Bag

{bag}

Estimated Fair Value:
€{round(fair_value)}

Asking Price:
€{asking_price}

Investment Score:
{investment_score}/100

Recommendation:
{recommendation}

Number of Comparable Sales:
{len(top_comparables)}

Requirements:

- Maximum 120 words
- Professional tone
- Explain WHY the recommendation makes sense
- Mention market pricing
- Mention comparable sales
- Do not invent facts
"""

    response = client.responses.create(
        model="gpt-5.1",
        input=prompt,
    )

    return response.output_text
