
"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.
    """
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


def _parse_query(query: str) -> dict:
    """
    Extract a simple description, size, and max_price from the user's query.
    """
    original_query = query
    query_lower = query.lower()

    max_price = None
    price_match = re.search(
        r"(?:under|below|less than|maximum|max)?\s*\$?(\d+(?:\.\d+)?)",
        query_lower,
    )

    if price_match and any(
        word in query_lower
        for word in ["under", "below", "less than", "maximum", "max", "$"]
    ):
        max_price = float(price_match.group(1))

    size = None
    size_match = re.search(r"\bsize\s+([a-z0-9/]+)\b", query_lower)

    if size_match:
        size = size_match.group(1).upper()

    description = query_lower

    description = re.sub(
        r"(under|below|less than|maximum|max)\s*\$?\d+(?:\.\d+)?",
        " ",
        description,
    )
    description = re.sub(r"\$\d+(?:\.\d+)?", " ", description)
    description = re.sub(r"\bsize\s+[a-z0-9/]+\b", " ", description)

    filler_phrases = [
        "i am looking for",
        "i'm looking for",
        "looking for",
        "can you find me",
        "find me",
        "show me",
        "what is out there",
        "what's out there",
        "how would i style it",
        "how can i style it",
        "how would i style",
        "how can i style",
        "mostly wear",
        "i mostly wear",
        "with",
        "and",
        "please",
    ]

    for phrase in filler_phrases:
        description = description.replace(phrase, " ")

    description = re.sub(r"[^a-z0-9\s/-]", " ", description)
    description = re.sub(r"\s+", " ", description).strip()

    if not description:
        description = original_query

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for one interaction.
    """
    session = _new_session(query, wardrobe)

    parsed = _parse_query(query)
    session["parsed"] = parsed

    description = parsed["description"]
    size = parsed["size"]
    max_price = parsed["max_price"]

    search_results = search_listings(
        description=description,
        size=size,
        max_price=max_price,
    )
    session["search_results"] = search_results

    if not search_results:
        session["error"] = (
            "I couldn't find any listings that match that exact request. "
            "Try increasing your budget, removing the size filter, or using a broader description."
        )
        session["selected_item"] = None
        session["outfit_suggestion"] = None
        session["fit_card"] = None
        return session

    selected_item = search_results[0]
    session["selected_item"] = selected_item

    outfit_suggestion = suggest_outfit(selected_item, wardrobe)
    session["outfit_suggestion"] = outfit_suggestion

    if not outfit_suggestion or not outfit_suggestion.strip():
        session["error"] = "I found an item, but I could not create an outfit suggestion."
        session["fit_card"] = None
        return session

    fit_card = create_fit_card(outfit_suggestion, selected_item)
    session["fit_card"] = fit_card

    if not fit_card or not fit_card.strip():
        session["error"] = "I created an outfit suggestion, but I could not create a fit card."
        return session

    return session


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")

    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )

    print("Parsed query:")
    print(session["parsed"])

    if session["error"]:
        print(f"\nError: {session['error']}")
    else:
        print(f"\nFound: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")

    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )

    print("Parsed query:")
    print(session2["parsed"])
    print(f"\nError message: {session2['error']}")
    print(f"Selected item: {session2['selected_item']}")
    print(f"Fit card: {session2['fit_card']}")
