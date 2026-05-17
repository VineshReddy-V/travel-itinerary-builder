# 🏗️ Architecture — Travel Itinerary Builder MCP Server

## Overview

The Travel Itinerary Builder follows the **Model Context Protocol (MCP)** client-server architecture. The project is an MCP **server** that exposes travel-related tools. An external **client** (Claude Desktop) connects to the server, discovers available tools, and orchestrates them to fulfill user requests.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Desktop (Client)                  │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │  User Prompt  │───>│  LLM (Claude)│───>│  Tool Router   │ │
│  └──────────────┘    └──────────────┘    └───────┬───────┘  │
│                                                   │          │
└───────────────────────────────────────────────────┼──────────┘
                                                    │
                                          MCP Protocol (stdio)
                                                    │
┌───────────────────────────────────────────────────┼──────────┐
│                   MCP Server (Python)              │          │
│                                                    ▼          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    FastMCP Router                        │ │
│  │                                                          │ │
│  │  ┌─────────────────┐ ┌──────────────┐ ┌──────────────┐  │ │
│  │  │search_destination│ │manage_        │ │generate_trip │  │ │
│  │  │_info             │ │itinerary     │ │_dashboard    │  │ │
│  │  └────────┬─────────┘ └──────┬───────┘ └──────┬───────┘  │ │
│  │           │                  │                 │          │ │
│  └───────────┼──────────────────┼─────────────────┼──────────┘ │
│              │                  │                 │            │
│              ▼                  ▼                 ▼            │
│  ┌──────────────────┐ ┌──────────────┐ ┌─────────────────┐   │
│  │  Tavily Search   │ │  Local File  │ │  Prefab UI      │   │
│  │  API (Internet)  │ │  System      │ │  (Dynamic HTML) │   │
│  └──────────────────┘ └──────────────┘ └─────────────────┘   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## MCP Client-Server Connection

### Transport: stdio (Standard Input/Output)

The server communicates with Claude Desktop over **stdio**:

1. **Claude Desktop spawns the server** as a subprocess using the path in `claude_desktop_config.json`.
2. **Handshake**: Client sends `initialize` request, server responds with capabilities.
3. **Tool Discovery**: Client calls `tools/list`, server returns tool schemas.
4. **Tool Execution**: Client sends `tools/call` with tool name and arguments, server executes and returns results.

```
Claude Desktop                          MCP Server
     │                                       │
     │──── initialize ─────────────────────>│
     │<─── capabilities ───────────────────│
     │                                       │
     │──── tools/list ─────────────────────>│
     │<─── [search_destination_info,        │
     │      manage_itinerary,               │
     │      generate_trip_dashboard] ───────│
     │                                       │
     │──── tools/call                        │
     │     name: search_destination_info     │
     │     args: {city: "Tokyo"} ──────────>│
     │                                       │
     │<─── result: "Top attractions..." ────│
     │                                       │
```

### No Client Code in This Project

This project is **server-only**. The client is Claude Desktop, which is an external application. We do not implement any MCP client code — Claude Desktop handles:
- Connecting to the server
- Discovering tools
- Deciding which tools to call (LLM reasoning)
- Passing tool results back to the LLM

---

## Tool Architecture

### Tool 1: `search_destination_info(city, query_type)`

**Purpose**: Internet search for travel information.

```
Input: city="Tokyo", query_type="attractions"
  │
  ▼
Constructs smart search query
  │  e.g., "best tourist attractions in Tokyo 2025"
  ▼
Tavily Search API (search_depth="basic")
  │
  ▼
Formats results: title, URL, content snippet
  │
  ▼
Output: Formatted string with numbered results
```

**Query types supported:**
| query_type | Search Query Pattern |
|------------|---------------------|
| `attractions` | "best tourist attractions in {city}" |
| `hotels` | "best hotels to stay in {city} with prices" |
| `budget` | "average travel budget for {city} daily costs" |
| `flights` | "cheapest flights to {city} from major cities" |
| `food` | "must-try local food and restaurants in {city}" |
| `tips` | "travel tips and safety advice for {city}" |
| `weather` | "best time to visit {city} weather by month" |
| (custom) | Direct pass-through to Tavily |

### Tool 2: `manage_itinerary(action, filepath, content)`

**Purpose**: Local file CRUD for itinerary persistence.

```
Actions:
  ┌─────────┐
  │ create  │──> Write new file (fails if exists)
  ├─────────┤
  │ read    │──> Read file contents (fails if missing)
  ├─────────┤
  │ update  │──> Append content to existing file
  ├─────────┤
  │ delete  │──> Remove file from filesystem
  └─────────┘
```

**Files the agent typically creates:**
- `trip_log.log` — Audit trail of agent actions
- `<city>_itinerary.md` — Structured day-by-day itinerary
- `<city>_budget.md` — Detailed budget breakdown

### Tool 3: `generate_trip_dashboard(python_code)`

**Purpose**: Dynamic Prefab UI generation.

```
Input: Python code string (written by the LLM)
  │
  ▼
exec(python_code) in sandboxed environment
  │
  ▼
Validates: 'app' variable exists and is PrefabApp
  │
  ├── Success → Returns PrefabApp (rendered as HTML in Claude Desktop)
  │
  └── Error → Returns error UI with Code block showing the exception
```

**Prefab components the agent can use:**

| Component | Travel Use Case |
|-----------|----------------|
| `Tabs` + `Tab` | Day-by-day itinerary (Day 1, Day 2, ...) |
| `Accordion` + `AccordionItem` | Expandable activity details per day |
| `Table` + `TableRow` | Budget breakdown, hotel comparisons |
| `Card` + `CardContent` | Attraction highlights, hotel cards |
| `Badge` | Trip status, budget level, category tags |
| `Alert` | Safety warnings, visa requirements |
| `Grid` + `GridItem` | Side-by-side layout for comparisons |
| `Carousel` | Featured attractions slideshow |
| `Heading` / `Text` / `Markdown` | Descriptions and formatted content |
| `Separator` | Visual section dividers |
| `Code` | Embedding audit log proof |

---

## Prompt Architecture

### `/plan_trip` Prompt Flow

```
User Input: "Tokyo, 5 days"
         │
         ▼
┌─────────────────────────────────────┐
│  PHASE 1: DESTINATION RESEARCH      │
│                                     │
│  search_destination_info("Tokyo",   │
│    "attractions")                   │
│  search_destination_info("Tokyo",   │
│    "hotels")                        │
│  search_destination_info("Tokyo",   │
│    "budget")                        │
│  search_destination_info("Tokyo",   │
│    "tips")                          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  PHASE 2: ITINERARY MANAGEMENT      │
│                                     │
│  manage_itinerary("create",         │
│    "trip_log.log", "Planning...")    │
│  manage_itinerary("create",         │
│    "tokyo_itinerary.md", <content>) │
│  manage_itinerary("read",           │
│    "tokyo_itinerary.md")            │
│  manage_itinerary("update",         │
│    "trip_log.log", "Verified...")    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  PHASE 3: DASHBOARD GENERATION      │
│                                     │
│  generate_trip_dashboard(           │
│    <python_code with Tabs,          │
│     Accordions, Tables, Badges>)    │
└─────────────────────────────────────┘
```

---

## Data Flow

```
Tavily API ──search results──> Claude LLM ──structured data──> manage_itinerary
                                    │                              │
                                    │                         Local Files
                                    │                         (.md, .log)
                                    │
                                    └──python code──> generate_trip_dashboard
                                                           │
                                                      Prefab UI HTML
                                                           │
                                                      Claude Desktop
                                                      (rendered in chat)
```

---

## Error Handling

| Scenario | Handling |
|----------|----------|
| Tavily API key missing | Returns error message, agent should inform user |
| Tavily search fails | Returns error string, agent can retry with different keywords |
| File already exists (create) | Returns error, agent should use "update" instead |
| File not found (read/update) | Returns error, agent should use "create" first |
| UI code syntax error | Returns error PrefabApp with `Code` block showing exception |
| UI code missing `app` variable | Returns error PrefabApp explaining the issue |

---

## Security Considerations

- **API keys** are stored in `.env` file (never committed to git)
- **File operations** are unrestricted — the agent can read/write anywhere the process has access. For production, consider sandboxing to a specific directory.
- **`exec()` for UI generation** runs agent-generated Python code. This is powerful but inherently risky. The execution is limited to the `prefab_ui` library scope.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `fastmcp[apps]` | MCP server framework with Prefab app support |
| `prefab-ui` | Dynamic UI component library (Python → HTML) |
| `tavily-python` | Web search API client |
| `python-dotenv` | Environment variable management |

---
