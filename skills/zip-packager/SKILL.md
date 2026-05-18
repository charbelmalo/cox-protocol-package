---
name: zip-packager
description: >
  Expert at assembling, verifying, and delivering the final design-spec ZIP package for the
  LLMAgentZipRecreation workflow. Use this skill for Step 09, or any time a user needs to
  compress a structured documentation folder into a verified, downloadable ZIP. Trigger on:
  "zip up the design specs", "create the final package", "compress and verify the output folder",
  "make a downloadable zip from these files", or when the zip-design-orchestrator delegates Step 09.
  Also useful standalone when a user has a folder of files they want packaged and verified before
  download.
---

# ZIP Packager

You are the expert for **Step 09** of the LLMAgentZipRecreation workflow. Your job is to assemble
all generated files into a verified, clean ZIP archive and deliver it to the user as a download link.

## Pre-Zip Quality Gate

Before creating the ZIP, run through this checklist. Report any failures to the orchestrator
rather than zipping a broken package.

### File Completeness Check

```bash
# List the project folder contents
ls -la {project_slug}_design_specs/
```

Verify:
- [ ] Every screenshot file (`*.png`, `*.jpg`, `*.webp`) has a matching `.design.md`
- [ ] Every screenshot file has a matching `.yaml`
- [ ] `README.md` is present
- [ ] `website_logic_and_functionality.md` is present
- [ ] `coding_agent_starting_point.md` is present
- [ ] `llm_agent_zip_recreation_instructions.yaml` is present
- [ ] No files named with timestamps (`image001`, `screenshot_2024...`, `crop_...`)
- [ ] No temp or partial files (`.tmp`, `.partial`, empty files)

### UTF-8 Check

```bash
# Verify text files are valid UTF-8
file {project_slug}_design_specs/*.md {project_slug}_design_specs/*.yaml
```

If any file shows encoding issues, flag it for the orchestrator to regenerate.

---

## Zip Assembly

```bash
# Create ZIP from the root design-specs folder
cd /home/claude  # or wherever the project folder lives
zip -r {project_slug}_full_design_and_build_docs.zip {project_slug}_design_specs/

# Verify the zip was created
ls -lh {project_slug}_full_design_and_build_docs.zip
```

---

## Zip Verification

After creating the ZIP, always verify its contents:

```bash
# List zip contents
unzip -l {project_slug}_full_design_and_build_docs.zip
```

Confirm:
- [ ] All expected files appear in the listing
- [ ] No paths outside the root folder (no absolute paths, no `..` traversal)
- [ ] File sizes look reasonable (non-zero for all files)
- [ ] ZIP opens successfully (no corruption)

---

## Extending an Existing ZIP

If the user already has a ZIP from a previous run:

```bash
# Unzip to a temp directory
mkdir -p /tmp/zip_extend_work
unzip existing_package.zip -d /tmp/zip_extend_work/

# Copy new/updated files into the unzipped folder
cp new_files/* /tmp/zip_extend_work/{existing_root_folder}/

# Recompress with a new descriptive name (don't overwrite original)
cd /tmp/zip_extend_work
zip -r /home/claude/{project_slug}_full_design_and_build_docs_v2.zip {existing_root_folder}/
```

**Never overwrite the original ZIP** unless the user explicitly requests it.

---

## Delivery

After successful verification, present the ZIP file to the user using `present_files`. Then provide
a brief completion note:

```
✓ ZIP package ready:
  • {N} screenshots renamed and included
  • {N} .design.md + .yaml spec pairs
  • 4 package-level docs (README, logic, build guide, recreation instructions)
  • Total size: {X}MB
```

Keep the note short — the user can inspect the file themselves.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| ZIP too large (>50MB) | Check for uncompressed video/image artifacts; exclude with `zip -x` |
| Missing spec pair | Flag to orchestrator; regenerate before zipping |
| Encoding error | Re-save file with `iconv -f latin1 -t utf-8` or regenerate |
| ZIP opens as empty | Check working directory; ensure relative path used in `zip` command |
| Duplicate filenames | Review slug uniqueness; one screenshot per slug only |
