# Contract → diagnostic → correction → artifact

The reproducible demonstration uses a manifest, one page and one action component. It establishes identity and evidence handling in the implemented COX compiler.

After installing the project, run from the source checkout:

```bash
python scripts/demo.py --out /tmp/cox-contract-demo
```

The directory must be new or empty. The script creates the starter, temporarily changes the component's `Slug` from `action_button` to `action_buton`, captures the actual `BINDING_MISMATCH` error, restores the correct value, validates three documents, compiles all targets into an external directory and verifies the ZIP inventory.

Read these artifacts in order:

1. `01-invalid-component.cox.txt`: the broken contract.
2. `02-diagnostic.json`: the real validator output, including file and field.
3. `03-corrected-component.cox.txt`: the single-field correction.
4. `04-result.json`: observed result and capability scope.
5. `build/react/`: typed scaffolding that retains evidence and intended behavior as comments.
6. `build/package/`: source/artifact ZIP and SHA-256 inventory.

The reference SVGs are illustrations of a proposed layout. They are not screenshots of a deployed application. The generated React uses structural `<main>` and `<section>` elements; an implementer supplies the real controls, styling and behavior.

This example checks a design-contract binding. It does not inspect rendered UI, evaluate an application's AST, or prove that the intended keyboard interaction has been implemented. A portfolio case study can show the concrete failure/recovery loop and explain these boundaries.
