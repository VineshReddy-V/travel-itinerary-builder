"""
Travel Itinerary Builder — MCP Server

Registers 3 MCP tools + 1 prompt via FastMCP:
  1. search_destination_info  — web search for travel data via Tavily
  2. manage_itinerary         — local file CRUD (create/read/update/delete)
  3. generate_trip_dashboard  — dynamic Prefab UI generation

Run:
    python mcp_server.py

Or connect via Claude Desktop (see README.md for config).
"""

import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from prefab_ui.app import PrefabApp
from prefab_ui.components import Column, Heading, Markdown, Card, Container

# Load environment variables from .env in the script's directory
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

# Initialize the MCP Server
mcp = FastMCP("Travel Itinerary Builder")

# ---------------------------------------------------------------------------
# Pre-built query templates for destination research
# ---------------------------------------------------------------------------
_QUERY_TEMPLATES = {
    "attractions": "best tourist attractions and must-visit places in {city} 2025",
    "hotels": "best hotels to stay in {city} with price range and ratings",
    "budget": "average daily travel budget for {city} including food transport accommodation",
    "flights": "cheapest flights to {city} from major cities with airlines and prices",
    "food": "must-try local food dishes and best restaurants in {city}",
    "tips": "essential travel tips safety advice and local customs for visiting {city}",
    "weather": "best time to visit {city} weather by month and what to pack",
    "transport": "best local transportation options in {city} for tourists",
    "nightlife": "best nightlife bars and entertainment in {city}",
    "shopping": "best shopping areas and local markets in {city}",
}


@mcp.tool()
def search_destination_info(city: str, query_type: str = "attractions") -> str:
    """Search the internet for travel information about a destination city.

    Args:
        city: The destination city to research (e.g., "Tokyo", "Paris", "Bangkok").
        query_type: The type of information to search for. Options:
            'attractions' — top tourist spots and must-visit places.
            'hotels'      — accommodation options with price ranges.
            'budget'      — average daily costs (food, transport, stays).
            'flights'     — flight prices and airlines from major hubs.
            'food'        — local cuisine and restaurant recommendations.
            'tips'        — safety advice, customs, visa info.
            'weather'     — best months to visit, what to pack.
            'transport'   — local transit options for tourists.
            'nightlife'   — bars, clubs, entertainment.
            'shopping'    — markets, malls, local crafts.
            Or pass any custom string to search directly.
    Returns:
        A formatted string containing the search results.
    """
    from tavily import TavilyClient

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY environment variable is not set."

    # Build the search query from template or use query_type as-is
    template = _QUERY_TEMPLATES.get(query_type.lower())
    if template:
        query = template.format(city=city)
    else:
        query = f"{query_type} in {city}"

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, search_depth="basic")

        results = response.get("results", [])
        if not results:
            return f"No results found for: {query}"

        output = [f"Travel Research — {city} ({query_type}):\n"]
        for i, res in enumerate(results, 1):
            output.append(f"{i}. {res.get('title')}")
            output.append(f"   URL: {res.get('url')}")
            output.append(f"   Content: {res.get('content')}\n")

        return "\n".join(output)
    except Exception as e:
        return f"Error performing search: {str(e)}"


@mcp.tool()
def manage_itinerary(action: str, filepath: str, content: str = "") -> str:
    """Perform CRUD operations on a local file to manage travel itineraries,
    budget logs, packing lists, or audit trails.

    Args:
        action: The operation to perform — 'create', 'read', 'update', or 'delete'.
        filepath: The path to the file (e.g., 'tokyo_itinerary.md', 'trip_log.log').
        content: The content to write or append (used for 'create' and 'update' only).
    Returns:
        A string indicating the result of the operation.
    """
    try:
        if action == "read":
            if not os.path.exists(filepath):
                return f"Error: File '{filepath}' does not exist."
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()

        elif action == "create":
            if os.path.exists(filepath):
                return f"Error: File '{filepath}' already exists. Use 'update' to modify."
            # Create parent directories if needed
            parent = os.path.dirname(filepath)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully created file '{filepath}'."

        elif action == "update":
            if not os.path.exists(filepath):
                return f"Error: File '{filepath}' does not exist. Use 'create' first."
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(f"\n{content}")
            return f"Successfully updated file '{filepath}'."

        elif action == "delete":
            if not os.path.exists(filepath):
                return f"Error: File '{filepath}' does not exist."
            os.remove(filepath)
            return f"Successfully deleted file '{filepath}'."

        else:
            return f"Error: Invalid action '{action}'. Use 'create', 'read', 'update', or 'delete'."

    except Exception as e:
        return f"Error performing {action} on {filepath}: {str(e)}"


@mcp.tool(app=True)
def generate_trip_dashboard(python_code: str) -> PrefabApp:
    """Executes the provided python_code to generate a dynamic travel dashboard
    using Prefab UI. The code MUST define and assign a valid PrefabApp object to
    a variable named `app`.

    Example python_code:
    ```python
    from prefab_ui.app import PrefabApp
    from prefab_ui.components import Column, Heading, Text, Badge

    with Column() as view:
        Heading("Tokyo 5-Day Trip")
        Badge("5 Days", variant="info")
        Text("Your personalized travel itinerary")
    app = PrefabApp(view=view)
    ```

    Available components you can import from prefab_ui.components:
        Layout:    Container, Column, Row, Grid(columns=N), GridItem, Separator
        Cards:     Card, CardHeader, CardTitle, CardContent
        Text:      Heading(content, level=N), Text(*args), Markdown(content), Code(content), Muted(content)
        Feedback:  Badge(label, variant=...), Alert(variant=...), AlertTitle(content), AlertDescription(content)
        Data:      Table, TableHeader, TableBody, TableRow, TableHead(content), TableCell(content)
        Nav:       Tabs, Tab(title=...), Accordion, AccordionItem(title=...), Carousel

    **CRITICAL API RULES — read carefully to avoid errors:**
        - Container components (Card, CardHeader, CardContent, Row, Column, Table,
          TableHeader, TableBody, TableRow, Tabs, Accordion, Alert) accept ONLY
          **kwargs — NO positional arguments. Use them as context managers:
              with CardHeader():
                  CardTitle("My Title")
          NEVER do: CardHeader(CardTitle("My Title"))  # THIS WILL CRASH
        - Leaf/text components accept a positional string:
              Heading("text"), Text("text"), Badge("label"), Code("text"),
              Muted("text"), CardTitle("text"), AlertTitle("text"),
              AlertDescription("text"), TableHead("text"), TableCell("text")
        - Tab uses `title=` NOT `label=`:  Tab(title="Day 1")
        - AccordionItem uses `title=`:  AccordionItem(title="Details")
        - Grid uses `columns=`:  Grid(columns=3)

    Tips for great travel dashboards:
        - Use Tabs for day-by-day itineraries (Day 1, Day 2, ...)
        - Use Accordion for expandable activity details
        - Use Table for budget breakdowns
        - Use Badge for trip status, budget level, weather
        - Use Alert for safety warnings or visa requirements
        - Use Card for attraction highlights
        - Use Grid for side-by-side hotel or restaurant comparisons

    Args:
        python_code: The Python code to execute that constructs the PrefabApp.
    """
    local_env = {}
    try:
        exec(python_code, globals(), local_env)

        if "app" in local_env and isinstance(local_env["app"], PrefabApp):
            return local_env["app"]
        else:
            from prefab_ui.components import Container, Heading, Text

            with Container() as view:
                Heading(
                    "UI Generation Error",
                    size="xl",
                    css_class="text-red-600 mb-4",
                )
                Text(
                    "The code executed successfully, but failed to assign "
                    "a valid PrefabApp to the variable 'app'."
                )
            return PrefabApp(view=view)

    except Exception as e:
        from prefab_ui.components import Container, Heading, Code

        with Container() as view:
            Heading(
                "Error Executing UI Code",
                size="xl",
                css_class="text-red-600 mb-4",
            )
            Code(str(e))
        return PrefabApp(view=view)


@mcp.prompt()
def plan_trip(destination: str) -> str:
    """Triggers a full travel research, itinerary creation, and dashboard
    generation workflow. Provide a destination and optional duration,
    e.g., 'Tokyo, 5 days' or 'Paris, 3 days'.
    """
    return f"""You are an elite, autonomous AI Travel Agent operating through an MCP Server.

YOUR MISSION: Plan a comprehensive, day-by-day travel itinerary for the following destination: '{destination}'

EXECUTE THE FOLLOWING WORKFLOW EXACTLY IN THIS ORDER:

### PHASE 1: DESTINATION RESEARCH (Multi-Hop Search)
Use the `search_destination_info` tool to gather comprehensive data. Make at least 3 searches:
1. Search with query_type="attractions" to find the best tourist spots and must-visit places.
2. Search with query_type="hotels" to find accommodation options with price ranges.
3. Search with query_type="budget" to understand average daily costs (food, transport, stays).
4. (Optional) Search with query_type="food" for local cuisine recommendations.
5. (Optional) Search with query_type="tips" for safety advice and local customs.

### PHASE 2: ITINERARY FILE MANAGEMENT (Advanced File CRUD)
Using ALL the research data you gathered, create a structured itinerary:
1. **Initialize Log:** Use `manage_itinerary` to `create` a file named `trip_log.log` stating: "Trip planning started for {destination}."
2. **Create Itinerary:** Use `manage_itinerary` to `create` a structured markdown file named `itinerary.md` containing:
   - Trip overview (destination, duration, budget estimate)
   - Day-by-day plan with morning/afternoon/evening activities
   - Hotel recommendations with price ranges
   - Budget breakdown (accommodation, food, transport, activities, miscellaneous)
   - Local tips and important notes
3. **Verify Integrity:** Use `manage_itinerary` to `read` `itinerary.md` to ensure the data is complete and correct.
4. **Finalize Log:** Use `manage_itinerary` to `update` `trip_log.log` appending: "Itinerary verified. Proceeding to dashboard generation."

### PHASE 3: DYNAMIC TRAVEL DASHBOARD (Prefab UI Generation)
Translate your itinerary into a stunning, interactive travel dashboard. Use the `generate_trip_dashboard` tool to write a Python script that uses `prefab_ui.components` to construct the layout. You must assign the final `PrefabApp` object to a variable named `app`.

**CRITICAL INSTRUCTIONS FOR DASHBOARD DESIGN:**
You are the lead UI/UX designer. Create a beautiful, travel-themed dashboard that includes:

1. **Header Section:** Use `Heading` for the trip title and `Badge` components for trip metadata (duration, budget level, best season).

2. **Day-by-Day Tabs:** Use `Tabs` and `Tab` to create one tab per day. Inside each tab, use `Card` components for each activity with:
   - Activity name and description
   - Estimated time and cost
   - `Badge` for activity type (Sightseeing, Food, Culture, Adventure, etc.)

3. **Budget Table:** Use `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell` to show a detailed budget breakdown with categories: Accommodation, Food, Transport, Activities, Miscellaneous, and Total.

4. **Tips & Alerts:** Use `Alert` with `AlertTitle` and `AlertDescription` for any safety warnings, visa requirements, or important travel advisories.

5. **Hotel Recommendations:** Use `Grid` and `Card` components to show 2-3 hotel options side by side with name, price, and rating as `Badge`.

**VALID COMPONENTS (do NOT hallucinate others):**
`Container`, `Column`, `Row`, `Grid`, `GridItem`, `Separator`, `Card`, `CardHeader`, `CardTitle`, `CardContent`, `Heading`, `Text`, `Markdown`, `Badge`, `Alert`, `AlertTitle`, `AlertDescription`, `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell`, `Tabs`, `Tab`, `Accordion`, `AccordionItem`, `Carousel`, `Code`, `Muted`.

**CRITICAL API RULES — FOLLOW EXACTLY OR THE CODE WILL CRASH:**
- Container components (Card, CardHeader, CardContent, CardFooter, Row, Column,
  Container, Table, TableHeader, TableBody, TableRow, Tabs, Accordion, Alert,
  Grid, GridItem) accept ONLY **kwargs. They take NO positional arguments.
  Always use them as context managers with `with ... :`.
  CORRECT:   `with CardHeader(): CardTitle("Title")`
  WRONG:     `CardHeader(CardTitle("Title"))`  ← CRASHES with "takes 1 positional argument but 2 were given"
- Tab uses `title=` parameter: `Tab(title="Day 1")`, NOT `Tab(label="Day 1")`.
- AccordionItem uses `title=`: `AccordionItem(title="Details")`.
- Grid uses `columns=`: `Grid(columns=3)`.
- IMPORTANT: "Divider" does NOT exist. Use "Separator" instead.
- Prove that your background tasks succeeded by embedding a `Code` block containing the final line of your `trip_log.log`.

Execute this entire workflow autonomously now, and SURPRISE the user with a beautiful travel dashboard!"""


if __name__ == "__main__":
    mcp.run()
