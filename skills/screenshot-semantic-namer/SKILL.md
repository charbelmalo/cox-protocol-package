---
name: screenshot-semantic-namer
description: >
  Expert at collecting, inspecting, and semantically renaming UI screenshots for design-spec packages.
  Use this skill for Steps 01 and 02 of the LLMAgentZipRecreation workflow, or any time the user
  needs to rename a set of screenshots using meaningful, implementation-friendly slugs. Trigger on
  phrases like "rename my screenshots", "give semantic names to these UI images", "organize these
  mockups", or when the zip-design-orchestrator delegates Steps 01–02. Also trigger when a user
  uploads multiple UI screenshots without clear names and asks to organize or document them.
---

# Screenshot Semantic Namer

You are the expert for **Steps 01 and 02** of the LLMAgentZipRecreation workflow. Your job is to
inspect every input screenshot, understand what UI section it depicts, and assign it a precise,
implementation-friendly semantic name.

## Step 01 — Collect and Inspect Inputs

1. List all supplied image files from `/mnt/user-data/uploads/` or the conversation context.
2. Visually examine each screenshot. Identify:
   - Is it a **full layout** (entire page view)?
   - A **cropped panel** (sidebar, header, footer, modal)?
   - A **card grid**, **analytics view**, **settings page**, **dashboard**, or other specific section?
3. Note whether any two screenshots look like the same section — flag duplicates but don't discard
   unless clearly redundant.

Output a brief inspection table before proceeding:

```
| File            | Identified Section      | Notes              |
|-----------------|-------------------------|--------------------|
| image001.png    | Left navigation sidebar | Has user profile   |
| image002.png    | Top header + KPI cards  | Search bar visible |
```

## Step 02 — Create Semantic Names

### Naming Rules

- Use **lowercase snake_case** exclusively
- Name by **section purpose**, not visual position or timestamp
- Be **specific**: `analytics_sidebar_panels` not just `sidebar`
- Avoid: dates, "screenshot", "crop", "temp", "untitled", index numbers alone

### Reference Slug Vocabulary

Use these patterns as inspiration — adapt to what you actually see:

| Pattern | Example Slugs |
|---|---|
| Navigation | `left_navigation_sidebar`, `top_navbar`, `breadcrumb_rail` |
| Headers | `top_header_stats_bar`, `page_header_with_search` |
| Card grids | `projects_grid_cards`, `templates_card_gallery` |
| Analytics | `analytics_sidebar_panels`, `commit_overview_chart`, `ai_usage_breakdown` |
| Modals | `new_project_modal`, `confirm_delete_dialog` |
| Settings | `account_settings_page`, `integrations_panel` |
| Empty states | `empty_projects_state`, `onboarding_welcome_screen` |
| Detail views | `project_detail_header`, `file_explorer_tree` |

### Action

For each screenshot:
1. Assign a semantic slug
2. Copy (or instruct the copy of) the file into the output folder using the slug as the new name,
   preserving the original extension (`.png`, `.jpg`, `.webp`, etc.)
3. Record the mapping for downstream skills to use

### Output Mapping Table

After renaming, produce this table for the orchestrator and downstream skills:

```
| Original File   | Semantic Slug                | New Filename                      |
|-----------------|------------------------------|-----------------------------------|
| image001.png    | left_navigation_sidebar      | left_navigation_sidebar.png       |
| image002.png    | top_header_stats_bar         | top_header_stats_bar.png          |
| image003.png    | projects_grid_cards          | projects_grid_cards.png           |
| image004.png    | analytics_sidebar_panels     | analytics_sidebar_panels.png      |
```

## Handling Edge Cases

- **Ambiguous section**: Use your best judgment, append `(inferred)` in the notes column, and ask
  the user to confirm before the ZIP is finalized.
- **Very similar screenshots**: Name them `{section}_state_running` and `{section}_state_stopped`
  to capture the difference.
- **Full-page screenshots that span multiple sections**: Pick the **dominant** section for the slug,
  note the secondary sections in the inspection table.
- **Only one screenshot**: That's fine — one slug, one spec pair.

## What You Hand Off

- A clean slug list (for use by visual-token-extractor and design-spec-writer)
- All renamed files copied into the project root folder
- The inspection + mapping tables (for the orchestrator's records)
