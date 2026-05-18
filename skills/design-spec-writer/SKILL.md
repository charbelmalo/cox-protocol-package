---
name: design-spec-writer
description: >
  Expert at writing per-screenshot design specification files in both human-readable compact markdown
  (.design.md) and machine-readable YAML (.yaml) formats, following the LLMAgentZipRecreation spec
  structure. Use this skill for Steps 04 and 05 of the LLMAgentZipRecreation workflow, or any time
  the user wants structured component specs generated from UI screenshots. Trigger on: "write design
  specs for these screenshots", "generate component YAML from this mockup", "document this UI section",
  "create .design.md files from these images", or when the zip-design-orchestrator delegates Steps
  04–05. Also valuable standalone when a developer or designer wants implementation-ready component
  documentation from any UI reference.
---

# Design Spec Writer

You are the expert for **Steps 04 and 05** of the LLMAgentZipRecreation workflow. For each renamed
screenshot, you produce two files:
- `{slug}.design.md` — human-readable, compact nested component format
- `{slug}.yaml` — machine-readable YAML component hierarchy

Both files reference the shared `VisualTokens` from the visual-token-extractor. Process each
screenshot one at a time, completing both files before moving to the next.

---

## Step 04 — Write `.design.md` (Human-Readable Spec)

### Format Rules

Use the **compact special nested component format**: nested `{Block: [...]}` syntax that reads as
markdown but describes design structure concisely.

```markdown
# {SectionName}

{SectionLayout: [desktop-first, glass surface, native macOS spacing]}
  {PrimaryRegion: [role, alignment, width behavior]}
  {SecondaryRegion: [role, alignment, width behavior]}

{ComponentName: [key visual traits, animation, states]}
  {SubComponent: {property: value} {property: value}}
  {Interaction: [hover, click, keyboard, drag, menu]}

{VisualTokens: [→ see shared visual_tokens block]}

{Responsive: [xl behavior, lg behavior, md behavior, sm behavior]}
```

### Required Sections

Every `.design.md` must contain:
1. **Section name** as H1
2. **Layout block** — overall structure, regions, alignment
3. **Component blocks** — one per major UI component visible in the screenshot
4. **VisualStyle reference** — pointer to shared visual tokens
5. **InteractionNotes** — hover, click, keyboard, drag, empty-state behaviors
6. **ResponsiveBehavior** — how the section adapts across breakpoints

### Component Writing Rules

- Describe **visible structure**, not product marketing copy
- Use **implementation vocabulary**: `grid`, `stack`, `row`, `panel`, `card`, `rail`, `toolbar`,
  `token`, `state`, `pill`, `badge`, `overlay`
- Note **states explicitly**: `default`, `hover`, `active`, `loading`, `empty`, `error`, `running`,
  `stopped`, `selected`
- Mark anything not clearly visible as `[Inferred]`

### Example Output

```markdown
# Projects Grid Cards

{ProjectsLayout: [main content area, desktop-first, fills remaining width after sidebar]}
  {GridRegion: [4-col xl, 3-col lg, 2-col md, 1-col sm, auto-fill with min-width]}
  {ControlsBar: [row above grid, sort dropdown + grid/list toggle, right-aligned]}

{ProjectCardsGrid: [glass surface, 8px gap, staggered fade-in on load]}
  {ProjectCard: [glass card, rounded-xl, hover lift, shadow elevation]}
    {ProjectInfo {Title: body text, black, bold, fills row} {ActionMenu: ellipsis, fixed width}}
    {ProjectCreativeVisual {PreviewStage: wide screenshot panel, clean perspective} {IconBadge: overlapping lower-left} {PortBadge: floating lower-right pill}}
    {ProjectMeta {Description: two-line clamp, muted} {StatsRow: stars + branches + last activity} {StatusDot: green running / amber stopped}}
  {Interaction: [hover → card lifts + shadow deepens, click → navigate to project detail]}

{EmptyState: [centered illustration + CTA button, shown when no projects exist]}

{Responsive: [4col-xl, 3col-lg, 2col-md, 1col-sm]}
```

---

## Step 05 — Write `.yaml` (Machine-Readable Spec)

### YAML Rules

- Valid YAML only — always verify indentation
- `PascalCase` keys for components
- Arrays for: responsive variants, states, supported controls
- Concise scalar values for styling tokens
- Reference `VisualTokens` at the top level — don't repeat token values inline

### Required Top-Level Keys

```yaml
Section: ""
Purpose: ""
Layout: {}
Components: {}
VisualStyle:
  Tokens: "→ shared VisualTokens block"
Interactions: []
Responsive: {}
ImplementationHints: []
```

### Component Pattern

```yaml
Components:
  ComponentName:
    Structure:
      - "Subpart description"
      - "Subpart description"
    Visual:
      Surface: "glass card"
      Border: "1px translucent stroke"
      Radius: "large (16px)"
      Shadow: "0 2px 8px rgba(0,0,0,0.08)"
    States:
      - default
      - hover
      - active
      - loading
    Behavior:
      Hover: "translateY -2px, shadow deepens"
      Active: "accent ring (2px blue-violet)"
      Empty: "placeholder illustration + CTA"
    DataBindings:
      - "projectId"
      - "status"
      - "lastAccessed"
```

### Card Grid Specific Pattern

```yaml
ProjectCardsGrid:
  Columns:
    xl: 4
    lg: 3
    md: 2
    sm: 1
  Gap: "8px"
  Sorting: true
  GridListToggle: true
  CardAnimation: "GSAP-friendly staggered fade + lift"
  VirtualScrolling: true  # Inferred for large sets
```

### Implementation Hints

Always include 2–4 `ImplementationHints` that an engineer can act on immediately:

```yaml
ImplementationHints:
  - "Use CSS grid with auto-fill and min-width for responsive columns"
  - "GSAP staggerFrom for card entry animation (delay: 0.05s per card)"
  - "Status dot color driven by project.status enum (running/stopped/paused/error)"
  - "Preview image cached at 400×240px, refreshed on project save"
```

---

## Processing Order

For each slug in the project:
1. Load (view) the renamed screenshot
2. Write the `.design.md`
3. Write the `.yaml`
4. Move to the next slug

Confirm completion of each pair before moving on:
> "✓ `projects_grid_cards.design.md` + `.yaml` written. Moving to `analytics_sidebar_panels`…"
