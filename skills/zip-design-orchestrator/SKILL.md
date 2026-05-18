---
name: zip-design-orchestrator
description: >
  Master orchestrator for producing a complete design-spec ZIP package from UI screenshots and
  conversational requirements. Use this skill whenever the user supplies screenshots (or crops, mockups,
  visual references) and wants a downloadable ZIP containing renamed screenshots, per-screenshot design
  specs (.design.md + .yaml), a logic doc, a coding-agent starting-point doc, a README, and this
  recreation instructions sheet. Trigger on phrases like "create a design spec ZIP", "generate design
  docs from screenshots", "make a build package from these mockups", "create an LLM agent ZIP",
  or any request to package UI screenshots into structured developer documentation.
---

# ZIP Design-Spec Orchestrator

You are the master coordinator for the LLMAgentZipRecreation workflow. Your job is to run all 9 steps
in order, delegating each step to the appropriate expert skill, and producing a complete, downloadable
ZIP package.

## Workflow Overview

```
Step 01 → screenshot-semantic-namer   (collect + inspect inputs)
Step 02 → screenshot-semantic-namer   (assign semantic slugs + rename)
Step 03 → visual-token-extractor      (extract shared design tokens)
Step 04 → design-spec-writer          (write per-screenshot .design.md)
Step 05 → design-spec-writer          (write per-screenshot .yaml)
Step 06 → package-docs-writer         (README.md)
Step 07 → package-docs-writer         (website_logic_and_functionality.md)
Step 08 → package-docs-writer         (coding_agent_starting_point.md)
Step 09 → zip-packager                (assemble, verify, deliver ZIP)
```

## How to Run

### 1. Capture Intent First

Before doing anything, confirm:
- The project slug (e.g. `product_ui` → folder `product_ui_design_specs`)
- All supplied screenshots (list them from `/mnt/user-data/uploads/` or inline images)
- Any product name, stack preferences, or special requirements the user has mentioned

### 2. Execute Steps Sequentially

Because steps feed into each other (semantic names from Step 02 are used by Steps 04–09), run them
in order. After each step, briefly confirm progress to the user before moving on.

**Steps 01–02 (screenshot-semantic-namer):**
- List all input images
- Visually inspect each one
- Assign a semantic slug per screenshot
- Copy renamed files into `{project_slug}_design_specs/`

**Step 03 (visual-token-extractor):**
- Analyze all screenshots together for a shared visual language
- Output a `visual_tokens` block used by Steps 04–05

**Steps 04–05 (design-spec-writer):**
- For each renamed screenshot, write `{slug}.design.md` and `{slug}.yaml`
- Use the visual tokens from Step 03
- Output all files into the root design-specs folder

**Steps 06–08 (package-docs-writer):**
- Write `README.md`, `website_logic_and_functionality.md`, `coding_agent_starting_point.md`
- Also copy `llm_agent_zip_recreation_instructions.yaml` (recreate from the canonical structure)

**Step 09 (zip-packager):**
- Verify every screenshot has a matching `.design.md` and `.yaml`
- Compress the root folder into `{project_slug}_full_design_and_build_docs.zip`
- Verify ZIP contents
- Present the download link

### 3. Output Structure

```
{project_slug}_design_specs/
├── {slug_1}.png                          ← renamed screenshot
├── {slug_1}.design.md                    ← human-readable design spec
├── {slug_1}.yaml                         ← machine-readable component spec
├── {slug_2}.png
├── {slug_2}.design.md
├── {slug_2}.yaml
├── ...
├── README.md
├── website_logic_and_functionality.md
├── coding_agent_starting_point.md
└── llm_agent_zip_recreation_instructions.yaml
```

Final ZIP: `{project_slug}_full_design_and_build_docs.zip`

## Handling Uncertainty

- If a screenshot's section is ambiguous, label it with a best-guess slug and note it as `(inferred)`.
- If the user hasn't supplied a project name, derive one from visible UI content or use `project_ui`.
- If extending an existing ZIP, unzip it first, append new content, recompress with an updated name.
- Never overwrite the original ZIP unless the user explicitly asks.

## Quality Gate Before Zipping

Before calling zip-packager, mentally run through this checklist:
- [ ] All screenshots renamed with semantic snake_case slugs
- [ ] Every screenshot has a matching `.design.md` AND `.yaml`
- [ ] Visual tokens are consistent across all spec files
- [ ] All 4 package docs are present
- [ ] No timestamp-named screenshots remain unless intentional
- [ ] All text files are UTF-8

## Communication Style

Keep the user informed between steps with brief status lines like:
> "✓ Step 02 complete — 5 screenshots renamed. Starting design spec generation…"

Don't dump all outputs at once — checkpoint at the end of each major phase.
