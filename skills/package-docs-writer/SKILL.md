---
name: package-docs-writer
description: >
  Expert at writing the four package-level documentation files for LLMAgentZipRecreation packages:
  README.md, website_logic_and_functionality.md, coding_agent_starting_point.md, and
  llm_agent_zip_recreation_instructions.yaml. Use this skill for Steps 06, 07, and 08 of the
  LLMAgentZipRecreation workflow, or any time a user needs product logic documentation or a
  coding-agent implementation guide generated from UI screenshots and requirements. Trigger on:
  "write the README for this design package", "create a logic doc from these mockups", "generate
  a coding agent starting point", "document the product behavior", or when the zip-design-orchestrator
  delegates Steps 06–08. Also useful standalone for generating developer onboarding docs from
  any set of UI references or product descriptions.
---

# Package Docs Writer

You are the expert for **Steps 06, 07, and 08** of the LLMAgentZipRecreation workflow. Your job is
to write the four package-level documents that make the ZIP useful for both humans and AI coding
agents. These docs synthesize everything learned from the screenshots and specs.

---

## Step 06 — `README.md`

Keep it **short** — this is a navigation document, not an essay.

```markdown
# {Project Name} Design Spec Package

This package was generated from {N} UI screenshots and contains everything needed to understand,
design, and implement the {product description}.

## Contents

| File | Type | Description |
|------|------|-------------|
| `{slug}.png` | Screenshot | Renamed UI reference: {section name} |
| `{slug}.design.md` | Human spec | Compact nested component design notes |
| `{slug}.yaml` | Machine spec | Parseable component hierarchy for agents |
| `README.md` | Guide | This file |
| `website_logic_and_functionality.md` | Logic | Product behavior, state machine, data flows |
| `coding_agent_starting_point.md` | Build | Implementation roadmap for AI coding agents |
| `llm_agent_zip_recreation_instructions.yaml` | Meta | How to recreate this package |

## How to Use

- **Designers**: Read `.design.md` files for layout and component guidance
- **Developers**: Parse `.yaml` files for component hierarchy; read logic doc for behavior
- **AI coding agents**: Start with `coding_agent_starting_point.md`, then reference `.yaml` specs
```

---

## Step 07 — `website_logic_and_functionality.md`

This is the **behavior bible**. Describe what the product does, how it works, and how data flows.
Derive as much as possible from the screenshots; mark inferences clearly.

### Required Sections

#### Product Purpose
What problem does this tool solve? Who uses it? One paragraph.

#### Core Entities
List the main data objects (e.g., Project, User, Tag, Provider, Port). For each:
- What is it?
- Key fields/attributes
- Relationships to other entities

#### Main User Flows
Numbered step-by-step flows for the 3–5 most important user journeys:
- Project discovery and launching
- Creating a new project
- Monitoring running services
- Viewing analytics/usage
- Filtering/searching

#### State Machine
Define all discrete states a core entity (usually Project) can be in:

```
running → stopped → paused → archived
       ↘ unhealthy → error
       ↗ indexing → ready
missing (not found on disk)
```

For each state: trigger, visual indicator, allowed transitions.

#### Local Runtime and Port Management
- How does the app detect running local services?
- How are ports assigned, tracked, and displayed?
- What happens when a port conflict occurs?

#### Health Monitoring
- How is project health determined?
- Polling interval, timeout logic, recovery behavior

#### Commit and Activity Analytics
- Data source (local git, API?)
- Aggregation window (7-day, 30-day)
- Chart types visible in screenshots

#### AI Usage Overview
- Up to 10 AI provider rows
- Metrics: requests, tokens/cost, usage percentage
- How is usage data collected and displayed?

#### Filtering, Sorting, Tags, Favorites
- Available sort fields and directions
- Tag creation, assignment, filtering logic
- Favorites behavior (pinned to top, star indicator)

#### Persistence Model
- What is stored locally vs. remotely?
- File formats (JSON, SQLite, config files)
- Cache invalidation strategy for previews

#### Error and Empty States
- Per-section empty state behavior
- Error recovery UX
- Missing project (directory deleted) handling

#### Security and Privacy Notes
- Is data sent to any remote service?
- Local-only vs. cloud-sync clarification
- Any auth flows visible in screenshots

### Writing Rules
- Separate **frontend behavior** from **backend responsibilities** clearly
- Use `[Inferred]` for behavior not directly visible in screenshots
- Prefer bullet lists and short paragraphs over walls of text

---

## Step 08 — `coding_agent_starting_point.md`

This is the **implementation guide** for an AI coding agent starting from scratch. It should be
specific enough that an agent can begin immediately without additional clarification.

### Required Sections

#### Mission
One sentence: what the agent is building and why.

#### Recommended Stack
List concrete technology choices:
```
Frontend: React + TypeScript + Tailwind CSS
Charts: Recharts or Chart.js
Animation: GSAP
Backend: Electron main process or Node.js local server
Data: SQLite (better-sqlite3) or JSON flat files
IPC: Electron IPC or REST on localhost
```
Mark as `[Suggested]` if the user didn't specify — agents should respect explicit stack choices.

#### Repository Structure
```
src/
├── main/          ← Electron/Node backend
├── renderer/      ← React frontend
│   ├── components/
│   │   ├── layout/
│   │   ├── cards/
│   │   ├── analytics/
│   │   └── shared/
│   ├── pages/
│   ├── hooks/
│   └── store/
├── shared/        ← Types shared between main + renderer
└── assets/
```

#### Data Models
TypeScript interfaces for all core entities, derived from spec YAML DataBindings fields.

```typescript
interface Project {
  id: string;
  name: string;
  path: string;
  status: 'running' | 'stopped' | 'paused' | 'unhealthy' | 'indexing' | 'missing' | 'archived';
  port?: number;
  tags: string[];
  starred: boolean;
  lastAccessed: Date;
  previewImagePath?: string;
  description?: string;
}
```

#### API Routes (if applicable)
```
GET  /api/projects          → list all projects
GET  /api/projects/:id      → single project
POST /api/projects/:id/start → launch project
POST /api/projects/:id/stop  → stop project
GET  /api/analytics/commits  → commit history
GET  /api/analytics/ai-usage → provider usage
```

#### UI Component Map
Map spec slugs to React component names:
```
left_navigation_sidebar   → <NavigationSidebar />
top_header_stats_bar      → <HeaderStatsBar />
projects_grid_cards       → <ProjectsGrid /> + <ProjectCard />
analytics_sidebar_panels  → <AnalyticsSidebar /> + <CommitsChart /> + <AIUsageTable />
```

#### Implementation Phases

**Phase 1 — Layout + Static Data** (start here)
- Set up project structure, design tokens in Tailwind config
- Build all layout shells with hardcoded mock data
- Implement navigation, header, card grid with static projects
- No backend integration yet

**Phase 2 — Core Interactions**
- Project card hover, click, action menu
- Grid/list toggle, sorting, filtering
- Status dots and badges with mock statuses

**Phase 3 — Backend Integration**
- File system scanning for projects
- Local server/process spawning
- Port detection and management
- Real project status polling

**Phase 4 — Analytics + AI Usage**
- Git log parsing for commit history
- Chart rendering with real data
- AI usage data ingestion

**Phase 5 — Polish**
- GSAP animations for card grid
- Preview screenshot generation and caching
- Error states, empty states, loading skeletons

#### Acceptance Criteria
- All sections from screenshots are rendered and interactive
- Project status updates reflect real local state
- Analytics charts render with real git/usage data
- App works offline (local-first)
- No destructive file operations without explicit confirmation

#### Testing Strategy
- Unit: data models, filtering, sorting logic
- Integration: file scanner, process manager, git parser
- E2E: core user flows (launch project, stop project, view analytics)

#### Non-Goals
- Remote project management (unless user specifies)
- Multi-user collaboration
- Mobile responsiveness (unless explicitly required)
- Cloud sync (unless explicitly required)

---

## Step 08b — `llm_agent_zip_recreation_instructions.yaml`

Copy the canonical `LLMAgentZipRecreationInstructions` YAML into this file verbatim. This ensures
any future agent can reproduce the package from scratch by following the same workflow.

If the source YAML is available in conversation context, copy it. Otherwise, note:
```yaml
# Source: LLMAgentZipRecreationInstructions canonical spec
# See conversation context or original system document for full content
```
