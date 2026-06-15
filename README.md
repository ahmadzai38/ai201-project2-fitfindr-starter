# FitFindr — Multi-Tool Thrifting Agent

FitFindr is a multi-tool AI agent that helps users find secondhand clothing items and figure out how to style them with their wardrobe. The agent searches a mock listings dataset, chooses a matching item, suggests an outfit, and creates a short shareable fit card/caption.

This project uses a local mock dataset instead of searching the internet. That means FitFindr can only find items that exist inside `data/listings.json`.

---

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_key_here
```

Run the app:

```bash
python app.py
```

Open the local URL shown in the terminal, usually:

```text
http://127.0.0.1:7860
```

---

## Dataset

The project uses `data/listings.json`, which contains 40 mock secondhand listings.

Each listing includes:

* `id`
* `title`
* `description`
* `category`
* `style_tags`
* `size`
* `condition`
* `price`
* `colors`
* `brand`
* `platform`

The project also uses wardrobe data from `data/wardrobe_schema.json`. I used the helper functions in `utils/data_loader.py`:

* `load_listings()`
* `get_example_wardrobe()`
* `get_empty_wardrobe()`

---

## Tool Inventory

### Tool 1: `search_listings(description, size, max_price)`

**Purpose:**
Searches the mock secondhand listings dataset for items that match the user's request.

**Inputs:**

* `description` (`str`): The clothing item or style the user is looking for, such as `"vintage graphic tee"`.
* `size` (`str | None`): The requested size, such as `"M"` or `"L"`. If no size is given, this can be `None`.
* `max_price` (`float | None`): The user's maximum budget. If no price is given, this can be `None`.

**Output:**

Returns a list of matching listing dictionaries. Each dictionary contains item information like title, price, size, platform, condition, colors, and style tags.

**Failure handling:**

If no items match, the tool returns an empty list `[]` instead of crashing.

---

### Tool 2: `suggest_outfit(new_item, wardrobe)`

**Purpose:**
Suggests one or two outfits using the selected thrifted item and the user's wardrobe.

**Inputs:**

* `new_item` (`dict`): The selected listing returned by `search_listings`.
* `wardrobe` (`dict`): The user's wardrobe, usually from `get_example_wardrobe()` or `get_empty_wardrobe()`.

**Output:**

Returns a string with outfit suggestions.

**Failure handling:**

If the wardrobe is empty, the tool still gives general styling advice instead of crashing. For example, it may suggest pairing the item with jeans, sneakers, boots, or a jacket.

---

### Tool 3: `create_fit_card(outfit, new_item)`

**Purpose:**
Creates a short shareable outfit caption based on the selected item and outfit suggestion.

**Inputs:**

* `outfit` (`str`): The outfit suggestion from `suggest_outfit`.
* `new_item` (`dict`): The selected listing from `search_listings`.

**Output:**

Returns a short caption-style string that could be used for an outfit post.

**Failure handling:**

If the outfit input is empty, the tool returns a clear error message instead of raising an exception.

---

## Planning Loop

The agent does not call all tools blindly. It uses conditional logic based on what happens at each step.

The planning loop works like this:

1. The user enters a natural language query.
2. The agent parses the query to extract:

   * description
   * size
   * maximum price
3. The agent calls `search_listings(description, size, max_price)`.
4. If no results are found:

   * the agent stores an error message in the session
   * the agent stops early
   * the agent does not call `suggest_outfit`
   * the agent does not call `create_fit_card`
5. If results are found:

   * the agent selects the top result
   * stores it as `session["selected_item"]`
6. The agent calls `suggest_outfit(selected_item, wardrobe)`.
7. The outfit suggestion is stored in `session["outfit_suggestion"]`.
8. The agent calls `create_fit_card(outfit_suggestion, selected_item)`.
9. The fit card is stored in `session["fit_card"]`.
10. The completed session is returned to the app.

This makes the agent behavior depend on state. For example, if search fails, the workflow stops early instead of trying to style a missing item.

---

## State Management

State is managed through a session dictionary in `agent.py`.

The session stores:

```python
{
    "query": query,
    "parsed": {},
    "search_results": [],
    "selected_item": None,
    "wardrobe": wardrobe,
    "outfit_suggestion": None,
    "fit_card": None,
    "error": None,
}
```

The most important state flow is:

```text
search_results
→ selected_item
→ outfit_suggestion
→ fit_card
```

The selected item returned by `search_listings` is passed into `suggest_outfit`. Then the outfit suggestion and selected item are passed into `create_fit_card`.

This shows state passing between tools without asking the user to re-enter information.

---

## Error Handling Strategy

| Tool              | Failure Mode               | Agent Response                                                                                                                                                                      |
| ----------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `search_listings` | No matching listings found | The agent returns an error message telling the user to increase the budget, remove the size filter, or use a broader description. It stops early and does not call the other tools. |
| `suggest_outfit`  | Wardrobe is empty          | The tool still gives general styling advice using common items like jeans, sneakers, boots, or jackets.                                                                             |
| `create_fit_card` | Outfit input is missing    | The tool returns: “I couldn't create a fit card because the outfit suggestion was missing.”                                                                                         |

Example no-results query tested:

```text
designer ballgown size XXS under $5
```

Agent response:

```text
I couldn't find any listings that match that exact request. Try increasing your budget, removing the size filter, or using a broader description.
```

---

## Testing

I tested each tool individually before connecting them to the agent.

Run tests with:

```bash
python -m pytest tests/
```

Current test result:

```text
7 passed
```

The tests cover:

* search returns results
* search returns `[]` for no matches
* price filtering works
* outfit suggestion works with example wardrobe
* outfit suggestion works with empty wardrobe
* fit card returns a caption
* fit card handles empty outfit input

I also tested the full app with:

```text
vintage graphic tee under $30
```

This completed the full workflow:

```text
search_listings → suggest_outfit → create_fit_card
```

I also tested the failure path with:

```text
designer ballgown size XXS under $5
```

This correctly stopped early and showed an error message.

---

## AI Usage

I used ChatGPT to help with this project in specific ways.

### Instance 1: Planning and tool design

I gave ChatGPT the project requirements and the `planning.md` template. It helped me write clear tool specifications for:

* `search_listings`
* `suggest_outfit`
* `create_fit_card`

I reviewed the plan before using it and made sure the tool names, inputs, outputs, and failure modes matched the starter code.

### Instance 2: Tool implementation

I used ChatGPT to help implement the functions in `tools.py`. I gave it the tool specifications from `planning.md` and asked it to implement one tool at a time.

Before trusting the code, I tested each tool from the terminal. I also fixed indentation issues and verified that each tool handled its failure case correctly.

### Instance 3: Agent loop and app connection

I used ChatGPT to help implement `run_agent()` in `agent.py` and `handle_query()` in `app.py`.

I verified the generated code by running:

```bash
python agent.py
python app.py
python -m pytest tests/
```

I also tested both the happy path and failure path in the Gradio interface.

---

## Spec Reflection

One way the spec helped me was that it made the workflow clear before I started coding. I knew that `search_listings` had to run first, and if it returned no results, the agent needed to stop early. That made the planning loop easier to implement.

One way the implementation diverged from the spec is that I used a simple regex/string parser for extracting price and size from the user query instead of using the LLM. I did this because it was simpler, faster, and easier to test for this project. The LLM is still used for outfit suggestions and fit card generation.

---

## Demo Video


Demo video link: [Watch the demo](https://drive.google.com/file/d/1z0FITJchc7szUEUK_xmTxFST9rvKBfPH/view?usp=sharing)

The demo should show:

1. A complete successful interaction using all three tools.
2. State passing from selected item to outfit suggestion to fit card.
3. A failure case where no listing is found and the agent responds gracefully.

Good demo queries:

```text
vintage graphic tee under $30
designer ballgown size XXS under $5
```

---

## Limitations

FitFindr does not search the live internet. It only searches the mock listings in `data/listings.json`.

For example, if a user searches for:

```text
Cristiano Ronaldo 2008 jersey
```

the app will only find it if that kind of item exists in the mock dataset. Otherwise, it will return the no-results error.
