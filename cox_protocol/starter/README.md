# COX example

This starter specifies an intended interface. Its SVG is an illustration, not evidence of a shipped product.

Run `cox validate .`, then `cox compile . --target all`. React output is structural scaffolding: supply actual styles, behavior and tests in the consuming app.

Change `EvidenceSummary.Intended` to an unknown level such as `Certain` to see a schema diagnostic; restore it and revalidate. `cox verify-package build/package/<project-slug>.zip` checks the archived file inventory.
