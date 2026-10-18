# COX Language Support

COX Language Support adds syntax highlighting, editor configuration, and authoring snippets for `.cox` files.

## Features

- Dedicated `cox` language registration for `.cox`
- YAML-derived tokenization via `source.yaml` grammar inclusion
- COX header highlighting for versioned metadata fields
- Authoring snippets for manifest, page, component, protocol, and crop metadata documents
- Installable VSIX packaging surface for local use or Marketplace preparation

## Included Snippets

- `cox-header`: common COX header
- `cox-manifest`: manifest skeleton
- `cox-page`: page spec skeleton
- `cox-component`: component spec skeleton
- `cox-protocol`: protocol doc skeleton
- `cox-crop`: crop metadata skeleton

## Packaging

Create a local VSIX package from this folder:

```bash
npm ci --prefix ../..
npm run package
```

## Notes

COX inherits YAML-like syntax highlighting through TextMate grammar inclusion, but native VS Code contribution points do not provide full JSON Schema validation for custom YAML-compatible languages. Schema validation remains available through the repository CLI and bundled schema files in the main COX project.
