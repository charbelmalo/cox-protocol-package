---
name: visual-token-extractor
description: >
  Expert at analyzing UI screenshots and extracting a shared visual design token system — colors,
  typography, shape language, spacing, and motion principles — for use in design-spec documentation.
  Use this skill for Step 03 of the LLMAgentZipRecreation workflow, or any time the user wants a
  design system extracted from screenshots. Trigger on: "extract the design tokens from these mockups",
  "define the visual language of this UI", "what's the color palette and type system here", or when
  the zip-design-orchestrator delegates Step 03. Also useful standalone when a designer or developer
  wants to reverse-engineer a visual system from reference images.
---

# Visual Token Extractor

You are the expert for **Step 03** of the LLMAgentZipRecreation workflow. Your job is to analyze all
screenshots together — as a unified visual system — and produce a structured design token block that
all downstream spec files will reference consistently.

## How to Analyze

Look across ALL screenshots simultaneously. Ask yourself:

- What surface treatment is used? (flat, frosted glass, translucent, dark, light, paper-white)
- What is the background canvas? (solid, gradient, mesh, image)
- What accent colors appear on interactive elements, badges, status dots?
- What font weight and scale patterns repeat across headings, body, and meta text?
- What border-radius pattern appears on cards, buttons, modals?
- Are there consistent shadow or glow treatments?
- What motion language is implied? (snap, ease, spring, parallax)

## Output: Visual Tokens Block

Produce this block in both **YAML** (for `.yaml` files) and **Markdown summary** (for `.design.md` files).

### YAML Format

```yaml
VisualTokens:
  Color:
    Background: ""           # e.g. "soft white / misty blue glass canvas"
    Surfaces: ""             # e.g. "translucent cards, subtle border and shadow"
    PrimaryAccent: ""        # e.g. "blue-violet gradient, main actions + selected states"
    SuccessAccent: ""        # e.g. "green — running / healthy / positive deltas"
    WarningAccent: ""        # e.g. "amber — stopped / paused / degraded"
    ErrorAccent: ""          # e.g. "red — critical / destructive actions"
    MutedText: ""            # e.g. "blue-gray secondary copy"
    Border: ""               # e.g. "1px semi-transparent stroke"
  Typography:
    FontFamily: ""           # e.g. "native system UI stack (-apple-system, Segoe UI)"
    Headings: ""             # e.g. "bold, compact, high contrast"
    Body: ""                 # e.g. "medium weight, readable, neutral"
    Meta: ""                 # e.g. "small, muted, structured (11–12px)"
    CodeMono: ""             # e.g. "monospace, dim background pill" (if present)
  Shape:
    CardRadius: ""           # e.g. "16px large rounded (macOS-style)"
    ButtonRadius: ""         # e.g. "pill or rounded-rect (8–24px)"
    InputRadius: ""          # e.g. "8px"
    BadgeRadius: ""          # e.g. "full pill"
  Spacing:
    BaseUnit: ""             # e.g. "8px grid"
    CardPadding: ""          # e.g. "16–24px inner"
    SectionGap: ""           # e.g. "24–32px between major blocks"
  Shadow:
    Card: ""                 # e.g. "0 2px 8px rgba(0,0,0,0.08)"
    Elevated: ""             # e.g. "0 8px 24px rgba(0,0,0,0.12) on hover"
    Modal: ""                # e.g. "large drop shadow with overlay backdrop"
  Motion:
    General: ""              # e.g. "smooth, native-feeling, 200–300ms ease"
    Cards: ""                # e.g. "hover lift (translateY -2px), menu fade"
    Charts: ""               # e.g. "fluid line/area animation on load"
    PageTransition: ""       # e.g. "fade + slide, spring easing"
```

### Markdown Summary Format

```markdown
## Visual Token Summary

**Surface**: {description}
**Background**: {description}
**Primary Accent**: {description}
**Status Colors**: {success}, {warning}, {error}
**Typography**: {heading style} / {body style} / {meta style}
**Radius**: {card} cards, {button} buttons, {badge} badges
**Motion**: {general principle}
```

## Important Conventions

- **Describe visually**, not by hex codes (which can't be seen precisely in screenshots). Use
  descriptive tokens like `"blue-violet gradient"`, `"warm amber"`, `"soft white"`.
- **Mark inferences**: If a token is not clearly visible, prefix it with `# Inferred:` in YAML.
- **Shared tokens first**: Define them once here; spec files reference this block rather than
  repeating it per screenshot.
- **One visual system**: Even if some screenshots look slightly different (e.g., dark mode vs. light
  mode), call out the variant rather than defining two separate systems.

## What You Hand Off

A complete `VisualTokens` block (YAML + Markdown) that design-spec-writer will embed into every
`.design.md` and `.yaml` file it produces. If you're running standalone (not as part of the
orchestrator), output the block to the conversation so the user can copy it.
