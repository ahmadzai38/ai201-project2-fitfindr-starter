"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    def words(value) -> list[str]:
        """Convert text/list values into clean lowercase words."""
        if value is None:
            return []

        if isinstance(value, list):
            value = " ".join(str(v) for v in value)
        else:
            value = str(value)

        value = value.lower()

        for ch in ["/", "-", "—", ".", ",", ":", ";", "(", ")", "[", "]", "{", "}", "'", '"', "!", "?"]:
            value = value.replace(ch, " ")

        return [word.strip() for word in value.split() if word.strip()]

    def size_matches(listing_size, requested_size) -> bool:
        """Match sizes safely. Example: M matches S/M, but L does not match W30 L30."""
        if requested_size is None or str(requested_size).strip() == "":
            return True

        listing_size_words = set(words(listing_size))
        requested_size_words = set(words(requested_size))

        return bool(listing_size_words.intersection(requested_size_words))

    stop_words = {
        "i", "am", "im", "looking", "for", "a", "an", "the", "and", "or",
        "under", "below", "less", "than", "with", "to", "wear", "mostly",
        "what", "would", "how", "style", "it", "me"
    }

    query_terms = {
        word for word in words(description)
        if word not in stop_words and len(word) > 1
    }

    if not query_terms:
        return []

    synonym_map = {
        "tee": {"shirt", "tshirt", "top"},
        "shirt": {"tee", "tshirt", "top"},
        "tshirt": {"tee", "shirt", "top"},
        "jeans": {"denim", "bottoms"},
        "denim": {"jeans"},
        "pants": {"trousers", "bottoms"},
        "trousers": {"pants", "bottoms"},
        "sneakers": {"shoes"},
        "boots": {"shoes"},
        "jacket": {"outerwear"},
        "hoodie": {"sweatshirt", "top"},
        "vintage": {"classic", "retro"},
    }

    expanded_terms = set(query_terms)
    for term in query_terms:
        expanded_terms.update(synonym_map.get(term, set()))

    scored_results = []

    for listing in listings:
        price = float(listing.get("price", 0))

        if max_price is not None and price > max_price:
            continue

        if not size_matches(listing.get("size", ""), size):
            continue

        title_terms = set(words(listing.get("title", "")))
        description_terms = set(words(listing.get("description", "")))
        category_terms = set(words(listing.get("category", "")))
        style_terms = set(words(listing.get("style_tags", [])))
        color_terms = set(words(listing.get("colors", [])))
        brand_terms = set(words(listing.get("brand", "")))
        platform_terms = set(words(listing.get("platform", "")))
        condition_terms = set(words(listing.get("condition", "")))

        all_listing_terms = (
            title_terms
            | description_terms
            | category_terms
            | style_terms
            | color_terms
            | brand_terms
            | platform_terms
            | condition_terms
        )

        overlap = expanded_terms.intersection(all_listing_terms)

        if not overlap:
            continue

        score = len(overlap)

        # Give extra weight to stronger fields.
        score += 2 * len(query_terms.intersection(title_terms))
        score += 2 * len(query_terms.intersection(style_terms))
        score += 1 * len(query_terms.intersection(category_terms))
        score += 1 * len(query_terms.intersection(description_terms))

        scored_results.append((score, price, listing))

    scored_results.sort(key=lambda item: (-item[0], item[1]))

    return [listing for score, price, listing in scored_results]
    


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.
    """
    items = wardrobe.get("items", []) if wardrobe else []

    item_title = new_item.get("title", "this thrifted item")
    item_price = new_item.get("price", "unknown price")
    item_platform = new_item.get("platform", "unknown platform")
    item_colors = ", ".join(new_item.get("colors", []))
    item_tags = ", ".join(new_item.get("style_tags", []))
    item_description = new_item.get("description", "")

    client = _get_groq_client()

    if not items:
        prompt = f"""
You are FitFindr, a helpful secondhand fashion styling assistant.

The user is considering this thrifted item:
- Title: {item_title}
- Price: ${item_price}
- Platform: {item_platform}
- Colors: {item_colors}
- Style tags: {item_tags}
- Description: {item_description}

The user's wardrobe is empty or not provided.

Give 1-2 useful outfit suggestions using general clothing pieces someone might own.
Be specific, casual, and practical. Mention that the wardrobe is limited, but still give helpful styling advice.
"""
    else:
        wardrobe_text = ""
        for item in items:
            name = item.get("name", "Unnamed item")
            category = item.get("category", "unknown category")
            colors = ", ".join(item.get("colors", []))
            tags = ", ".join(item.get("style_tags", []))
            notes = item.get("notes") or "No notes"
            wardrobe_text += (
                f"- {name} | category: {category} | colors: {colors} | "
                f"style tags: {tags} | notes: {notes}\n"
            )

        prompt = f"""
You are FitFindr, a helpful secondhand fashion styling assistant.

The user is considering this thrifted item:
- Title: {item_title}
- Price: ${item_price}
- Platform: {item_platform}
- Colors: {item_colors}
- Style tags: {item_tags}
- Description: {item_description}

The user's current wardrobe:
{wardrobe_text}

Suggest 1-2 complete outfits using the thrifted item and named pieces from the wardrobe.
Be specific. Mention actual wardrobe items by name.
Keep the answer short, natural, and useful.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a concise and practical fashion styling assistant.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.7,
            max_tokens=350,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return (
            f"I could not generate a full outfit suggestion because the styling tool failed: {e}. "
            f"Try pairing {item_title} with simple basics like jeans, sneakers, boots, or a neutral jacket."
        )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.
    """
    if not outfit or not outfit.strip():
        return "I couldn't create a fit card because the outfit suggestion was missing."

    if not new_item:
        return "I couldn't create a fit card because the thrifted item information was missing."

    item_title = new_item.get("title", "this thrifted item")
    item_price = new_item.get("price", "unknown price")
    item_platform = new_item.get("platform", "unknown platform")
    item_colors = ", ".join(new_item.get("colors", []))
    item_tags = ", ".join(new_item.get("style_tags", []))

    prompt = f"""
You are FitFindr, a secondhand fashion assistant.

Create a short, shareable outfit caption for this thrifted find.

Thrifted item:
- Title: {item_title}
- Price: ${item_price}
- Platform: {item_platform}
- Colors: {item_colors}
- Style tags: {item_tags}

Outfit suggestion:
{outfit}

Rules:
- Write 2-4 short sentences.
- Sound casual and authentic, like a real outfit post.
- Mention the item name, price, and platform naturally.
- Capture the outfit vibe in specific terms.
- Do not sound like a product description.
- Do not use hashtags unless they feel natural.
"""

    try:
        client = _get_groq_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You write short, stylish, casual outfit captions.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.95,
            max_tokens=180,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return (
            f"I couldn't create a fit card because the caption tool failed: {e}. "
            f"Outfit idea: {outfit}"
        )