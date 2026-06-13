# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**

`search_listings` searches the mock secondhand clothing listings dataset for items that match the user's requested description, size, and maximum price. It filters the listings using the available fields in the dataset, such as title, description, category, style tags, size, price, brand, platform, condition, and colors.

**Input parameters:**

* `description` (str): The item or style the user is looking for, such as `"vintage graphic tee"` or `"black jacket"`.
* `size` (str): The user's requested size, such as `"S"`, `"M"`, `"L"`, or `None` if the user does not give a size.
* `max_price` (float): The highest price the user is willing to pay, such as `30.0`.

**What it returns:**

It returns a list of matching listing dictionaries. Each result may include fields such as:

* `id`: unique listing ID
* `title`: item name
* `description`: short item description
* `category`: item category
* `style_tags`: list of style keywords
* `size`: item size
* `condition`: item condition
* `price`: item price
* `colors`: list of colors
* `brand`: item brand
* `platform`: where the item is listed

The list should be sorted so the most relevant or best matching items appear first.

**What happens if it fails or returns nothing:**

If no listings match the user's request, the tool returns an empty list `[]`. The agent should not call `suggest_outfit` or `create_fit_card` with empty search results. Instead, the agent should tell the user that no listings were found and suggest changing the search, such as increasing the budget, removing the size filter, or using a broader description.

---

### Tool 2: suggest_outfit

**What it does:**

`suggest_outfit` takes the selected listing from `search_listings` and the user's wardrobe, then suggests a complete outfit using the new item and existing wardrobe pieces. It should explain how the user can style the item in a natural and helpful way.

**Input parameters:**

* `new_item` (dict): The selected listing returned from `search_listings`. This includes fields like title, price, size, colors, condition, brand, platform, and style tags.
* `wardrobe` (dict): The user's wardrobe data. It contains the items the user already owns, such as pants, shoes, jackets, or accessories.

**What it returns:**

It returns a string containing one or more outfit suggestions. The suggestion should mention the new item and connect it with wardrobe pieces when possible. For example, it might suggest pairing a vintage tee with baggy jeans and chunky sneakers.

**What happens if it fails or returns nothing:**

If the wardrobe is empty or very minimal, the tool should still return a useful styling suggestion using general outfit advice. It should not crash. The response should clearly say that the wardrobe was limited and then suggest common pieces the user could wear with the item.

---

### Tool 3: create_fit_card

**What it does:**

`create_fit_card` creates a short, shareable outfit caption based on the outfit suggestion and the selected new item. The caption should sound like something a person might post on Instagram or share with friends, not like a boring product description.

**Input parameters:**

* `outfit` (str): The outfit suggestion returned by `suggest_outfit`.
* `new_item` (dict): The selected listing returned from `search_listings`.

**What it returns:**

It returns a short string, usually 1–3 sentences, that describes the outfit in a stylish and shareable way. It may mention the item, the platform, the price, and the overall outfit vibe.

**What happens if it fails or returns nothing:**

If the outfit string is empty or the selected item is missing, the tool should return a clear error message instead of crashing. The agent should show the error message to the user and explain that it could not create a fit card because the outfit information was incomplete.

---

### Additional Tools (if any)

No additional tools for the required version. I will focus on the three required tools first before adding any stretch features.

---

## Planning Loop

**How does your agent decide which tool to call next?**

The agent starts with the user's natural language query. It extracts or receives the main item description, size, maximum price, and wardrobe information. Then it uses a planning loop that checks the current session state and decides which tool should run next.

The loop follows this conditional logic:

1. Start with an empty session dictionary.
2. Store the original user query in the session.
3. Call `search_listings(description, size, max_price)`.
4. Store the search results in `session["search_results"]`.
5. If `search_results` is empty:

   * Set `session["error"]` to a helpful no-results message.
   * Set `session["selected_item"]`, `session["outfit_suggestion"]`, and `session["fit_card"]` to `None`.
   * Return the session early.
   * Do not call `suggest_outfit` or `create_fit_card`.
6. If `search_results` is not empty:

   * Choose the first result as the selected item.
   * Store it in `session["selected_item"]`.
7. Call `suggest_outfit(session["selected_item"], wardrobe)`.
8. Store the result in `session["outfit_suggestion"]`.
9. If the outfit suggestion is missing or empty:

   * Set `session["error"]` to a helpful message.
   * Return the session early.
10. Call `create_fit_card(session["outfit_suggestion"], session["selected_item"])`.
11. Store the result in `session["fit_card"]`.
12. Return the final session with the search results, selected item, outfit suggestion, fit card, and any error message.

The planning loop is not just a fixed sequence because it changes behavior based on what each tool returns. For example, if `search_listings` returns no results, the agent stops early instead of calling the next tools with bad input.

---

## State Management

**How does information from one tool get passed to the next?**

The agent stores information in a session dictionary during one interaction. This lets each tool use information returned by earlier tools without asking the user to re-enter it.

The session tracks:

* `session["query"]`: the original user request
* `session["description"]`: the item description extracted from the request
* `session["size"]`: the requested size, if provided
* `session["max_price"]`: the maximum price, if provided
* `session["wardrobe"]`: the user's wardrobe data
* `session["search_results"]`: the list returned by `search_listings`
* `session["selected_item"]`: the chosen listing, usually the first search result
* `session["outfit_suggestion"]`: the string returned by `suggest_outfit`
* `session["fit_card"]`: the caption returned by `create_fit_card`
* `session["error"]`: an error message if something fails

The most important state flow is:

`search_listings` returns a list of items → the agent stores the first item as `selected_item` → `selected_item` is passed into `suggest_outfit` → the outfit suggestion is stored → the outfit suggestion and selected item are passed into `create_fit_card`.

This proves that information is passed across tools in the same session instead of being hardcoded or re-entered by the user.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool            | Failure mode                          | Agent response                                                                                                                                                                                                                |
| --------------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| search_listings | No results match the query            | The agent says: “I couldn’t find any listings that match that exact request. Try increasing your budget, removing the size filter, or using a broader description.” The agent stops early and does not call the other tools.  |
| suggest_outfit  | Wardrobe is empty                     | The agent says the wardrobe is empty or limited, then gives general styling advice using common pieces like jeans, sneakers, boots, jackets, or neutral basics. The agent continues if a useful outfit suggestion is created. |
| create_fit_card | Outfit input is missing or incomplete | The agent returns a clear message such as: “I couldn’t create a fit card because the outfit suggestion was missing.” The agent does not crash and shows the user the issue.                                                   |

---

## Architecture

```text
User query
    |
    v
Planning Loop
    |
    |-- Extract description, size, max_price, wardrobe
    |
    v
search_listings(description, size, max_price)
    |
    |-- results = []
    |       |
    |       v
    |   Session["error"] = "No listings found..."
    |       |
    |       v
    |   Return session early
    |
    |-- results = [item1, item2, ...]
            |
            v
    Session["search_results"] = results
    Session["selected_item"] = results[0]
            |
            v
suggest_outfit(selected_item, wardrobe)
            |
            |-- outfit missing or empty
            |       |
            |       v
            |   Session["error"] = "Could not create outfit suggestion."
            |       |
            |       v
            |   Return session early
            |
            |-- outfit suggestion created
                    |
                    v
        Session["outfit_suggestion"] = outfit_suggestion
                    |
                    v
create_fit_card(outfit_suggestion, selected_item)
                    |
                    |-- fit card missing or error
                    |       |
                    |       v
                    |   Session["error"] = "Could not create fit card."
                    |
                    |-- fit card created
                            |
                            v
                Session["fit_card"] = fit_card
                            |
                            v
                    Return final session to app.py
```

---

## AI Tool Plan

**Milestone 3 — Individual tool implementations:**

I will use ChatGPT to help implement each tool one at a time. For `search_listings`, I will give ChatGPT the Tool 1 section of this planning.md and ask it to implement `search_listings(description, size, max_price)` in `tools.py` using `load_listings()` from `utils/data_loader.py`. Before using the code, I will check that it filters by description, size, and max price, and that it returns `[]` when there are no matches.

For `suggest_outfit`, I will give ChatGPT the Tool 2 section and ask it to implement the function using Groq with the model `llama-3.3-70b-versatile`. I will verify that it accepts `new_item` and `wardrobe`, handles an empty wardrobe, and returns a helpful string instead of crashing.

For `create_fit_card`, I will give ChatGPT the Tool 3 section and ask it to implement the function using Groq. I will verify that it accepts both `outfit` and `new_item`, returns a short caption, and handles an empty outfit string with a clear error message.

I will test each tool in isolation before connecting them to the agent. I will use pytest tests for normal cases and failure cases.

**Milestone 4 — Planning loop and state management:**

I will use ChatGPT to help implement the planning loop in `agent.py`. I will give it the Planning Loop, State Management, Error Handling, and Architecture sections of this planning.md. I will ask it to implement `run_agent()` so that it stores values in the session dictionary and branches correctly when a tool returns an empty result.

Before trusting the generated code, I will check that:

* The agent calls `search_listings` first.
* The agent stops early if search results are empty.
* The agent stores `selected_item` in the session.
* The agent passes `selected_item` into `suggest_outfit`.
* The agent passes `outfit_suggestion` and `selected_item` into `create_fit_card`.
* The agent does not call all tools unconditionally.
* The final session contains search results, selected item, outfit suggestion, fit card, and error if needed.

I will then test the happy path and the no-results path from the terminal before running the Gradio app.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**

The agent reads the user query and identifies the item description as `"vintage graphic tee"`, the maximum price as `30.0`, and the size as `None` if the user does not provide a specific size.

The agent calls:

`search_listings(description="vintage graphic tee", size=None, max_price=30.0)`

The tool searches the mock listings dataset and returns a list of matching secondhand items.

**Step 2:**

The agent checks the search results.

If the result list is empty, the agent stores an error message in the session and returns early.

If the result list contains items, the agent stores the list in `session["search_results"]` and chooses the first listing as `session["selected_item"]`.

Example selected item:

`"Faded Band Tee" — $22, size M, Depop, good condition`

**Step 3:**

The agent uses the selected item and the user's wardrobe to create an outfit suggestion.

The agent calls:

`suggest_outfit(new_item=session["selected_item"], wardrobe=session["wardrobe"])`

The tool returns a styling suggestion, such as pairing the tee with baggy jeans and chunky sneakers for a relaxed vintage streetwear look.

The agent stores this result in `session["outfit_suggestion"]`.

**Step 4:**

The agent uses the outfit suggestion and the selected item to create a shareable fit card.

The agent calls:

`create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])`

The tool returns a short caption-style outfit description.

The agent stores this result in `session["fit_card"]`.

**Final output to user:**

The user sees:

1. The selected listing, including title, price, platform, size, and condition.
2. A suggested outfit using the new item and wardrobe pieces.
3. A short fit card/caption they can share.

Example final response:

Selected item: Faded Band Tee — $22 on Depop, size M, good condition.

Outfit suggestion: Pair it with baggy jeans and chunky sneakers for a relaxed vintage streetwear look. Add a simple jacket if you want the outfit to feel more complete.

Fit card: thrifted this faded band tee for $22 and it fits perfectly with the baggy denim + chunky sneaker vibe. easy vintage look without trying too hard.
