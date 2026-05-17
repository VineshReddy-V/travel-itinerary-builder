# 🌍 Travel Itinerary Builder — MCP Server

Welcome to the **Travel Itinerary Builder**! This repository hosts an advanced **Model Context Protocol (MCP)** server built in Python using **FastMCP** and **Prefab-UI**.

This server acts as a robust backend for AI Agents (like Claude Desktop), giving them the autonomous ability to research travel destinations, manage itinerary files on your local filesystem, and **generate dynamic, highly customized travel dashboards on the fly**.

---

## ✨ Core Capabilities

The MCP server equips the AI with three powerful tools and one dynamic prompt:

### 🛠️ Tools
1. **`search_destination_info(city: str, query_type: str)`**: Leverages the [Tavily Search API](https://tavily.com/) to research travel destinations — attractions, hotels, flights, weather, local tips, and budget estimates.
2. **`manage_itinerary(action, filepath, content)`**: Provides full local CRUD capabilities, allowing the agent to automatically create itinerary markdown files, append day-by-day plans, maintain budget logs, and manage packing lists.
3. **`generate_trip_dashboard(python_code: str)`**: Instead of using static UI templates, the agent writes pure Python scripts utilizing `prefab-ui` components. The server executes this code in a sandbox and renders interactive components (Tabs for day-by-day plans, Accordions for activities, Tables for budgets, Badges for trip status, etc.) dynamically directly inside the chat interface!

### 🎯 Prompts
- **`/plan_trip`**: Users simply provide a destination city and number of days (e.g., "Paris, 5 days"). The server injects a comprehensive set of instructions guiding the agent to research the destination, build a day-by-day itinerary, save it locally, and generate a stunning travel dashboard.

---

## 🏗️ Architecture

```
User (Claude Desktop)
     │  "Plan a 5-day trip to Tokyo"
     ▼
Claude (Orchestrator)
     │  reads tool descriptions, decides what to call and in what order
     │
     ├─► PHASE 1: DESTINATION RESEARCH
     │       │
     │       ├── search_destination_info("Tokyo", "attractions")
     │       │     → Tavily Search → top attractions, temples, markets
     │       │
     │       ├── search_destination_info("Tokyo", "hotels")
     │       │     → Tavily Search → hotel recommendations, price ranges
     │       │
     │       ├── search_destination_info("Tokyo", "budget")
     │       │     → Tavily Search → average costs, transport, food prices
     │       │
     │       └── search_destination_info("Tokyo", "local_tips")
     │             → Tavily Search → best time to visit, customs, safety
     │
     ├─► PHASE 2: ITINERARY FILE MANAGEMENT
     │       │
     │       ├── manage_itinerary("create", "trip_log.log", "Trip planning started for Tokyo.")
     │       │     → Creates audit log
     │       │
     │       ├── manage_itinerary("create", "tokyo_itinerary.md", "<full itinerary>")
     │       │     → Creates structured markdown itinerary with day-by-day plan
     │       │
     │       ├── manage_itinerary("read", "tokyo_itinerary.md")
     │       │     → Verifies file integrity
     │       │
     │       └── manage_itinerary("update", "trip_log.log", "Itinerary verified. Building dashboard.")
     │             → Finalizes audit log
     │
     └─► PHASE 3: DYNAMIC DASHBOARD
             │
             └── generate_trip_dashboard(<python_code>)
                   → Agent writes Prefab UI Python code
                   → Tabs for each day, Accordion for activities
                   → Budget pie chart, packing checklist
                   → Renders interactive dashboard in Claude Desktop
```

### Why this is MCP:
- **Claude Desktop** is the **orchestrator** — it reads the user's intent and decides which tools to invoke.
- Each tool is **independent and specialized** — search handles web research, file CRUD handles persistence, UI handles visualization.
- The **MCP protocol** is the communication layer — tools are discovered dynamically, and results stream back to Claude in real time.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| MCP framework | [FastMCP](https://github.com/jlowin/fastmcp) — tool registration, async context |
| Orchestrator | Claude Desktop (claude-sonnet / claude-opus) |
| Web search | [Tavily Search API](https://tavily.com/) — real-time destination research |
| Dashboard UI | [Prefab-UI](https://github.com/prefab-ui/prefab-ui) (Python DSL → Tailwind + React) |
| Config | python-dotenv — API keys in `.env` |

---

## 🚀 Getting Started

### 1. Prerequisites
You will need a **Tavily API Key** to power the agent's web search capabilities.
- Sign up at [tavily.com](https://tavily.com/) to get a free API key.

### 2. Local Setup
```bash
# 1. Clone the repository
git clone <your-repo-url>
cd travel-mcp

# 2. Set up your environment variables
cp .env.example .env
# Edit .env and add your TAVILY_API_KEY

# 3. Create a virtual environment & install dependencies
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 3. Connect to Claude Desktop
To integrate this server with the Claude Desktop app, edit your configuration file:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the following:

```json
{
  "mcpServers": {
    "travel-itinerary": {
      "command": "C:\\absolute\\path\\to\\travel-mcp\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\absolute\\path\\to\\travel-mcp\\mcp_server.py"
      ]
    }
  }
}
```
*(Remember to replace the paths with the actual absolute paths on your machine!)*

Restart Claude Desktop for the changes to take effect.

---

## 🧠 How to Use It

1. Open Claude Desktop.
2. Click on the **Prompts** menu or type the slash command: `/plan_trip`.
3. Enter a destination and trip duration (e.g., "Tokyo, 5 days" or "Paris, 3 days").
4. **Sit back and watch the magic:**
   - Claude will research attractions, hotels, budgets, and local tips via Tavily.
   - Claude will create a structured markdown itinerary and audit log on your filesystem.
   - Claude will write Python code and generate a custom travel dashboard featuring Day-by-Day Tabs, Budget Tables, Activity Accordions, and Status Badges inside the chat!

---

## 📁 Project Structure

```
travel-mcp/
│
├── mcp_server.py              ← MCP server with 3 tools + 1 prompt
├── requirements.txt           ← Python dependencies
├── .env                       ← Your local config (TAVILY_API_KEY)
├── .env.example               ← Config template
├── README.md                  ← This file
├── ARCHITECTURE.md            ← Detailed architecture documentation
└── mcp_agent_prompt.txt       ← Reference prompt for manual use
```

**Generated files (created by the agent at runtime):**
```
├── trip_log.log               ← Audit log tracking agent workflow
├── <city>_itinerary.md        ← Structured markdown itinerary
└── <city>_budget.md           ← Budget breakdown (optional)
```

---

## 💬 Example Prompts

```
Plan a 5-day trip to Tokyo, save the itinerary, and show me a trip dashboard.
Build a 3-day budget itinerary for Bangkok under $500.
Research the best attractions in Rome and create a visual travel guide.
Plan a honeymoon trip to Bali — 7 days, luxury budget.
Create a weekend getaway plan for Goa with local food recommendations.
```

---

## 📊 Dashboard Features (Prefab UI)

The agent dynamically generates dashboards using these Prefab components:

- **Tabs** — One tab per day of the trip
- **Accordion** — Expandable activity details per day
- **Table** — Budget breakdown (accommodation, food, transport, activities)
- **Badge** — Trip status, budget level, weather alerts
- **Alert** — Safety warnings, visa requirements, travel advisories
- **Card** — Attraction highlights with descriptions
- **Grid** — Side-by-side comparisons (hotels, restaurants)
- **Carousel** — Photo-worthy attraction highlights

---

*Built with ❤️ for travel lovers and agentic AI workflows.*
