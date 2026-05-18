#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptPath = fileURLToPath(import.meta.url);
const packageRoot = path.resolve(path.dirname(scriptPath), "..");
const python = process.env.COX_PYTHON || "python3";
const pythonPath = [packageRoot, process.env.PYTHONPATH]
  .filter(Boolean)
  .join(path.delimiter);
const pythonEnv = {
  ...process.env,
  PYTHONPATH: pythonPath,
};

const dependencyCheck = spawnSync(
  python,
  ["-c", "import typer, yaml, jsonschema, rich"],
  {
    cwd: process.cwd(),
    env: pythonEnv,
    stdio: "pipe",
  },
);

if (dependencyCheck.status !== 0) {
  console.error(
    `Python dependencies for COX are missing in ${python}.`,
  );
  console.error(
    "Install them with `python3 -m pip install PyYAML jsonschema typer rich` or point COX_PYTHON at an environment that already has them.",
  );
  process.exit(dependencyCheck.status ?? 1);
}

const result = spawnSync(
  python,
  ["-m", "tools.cox_cli", ...process.argv.slice(2)],
  {
    cwd: process.cwd(),
    env: pythonEnv,
    stdio: "inherit",
  },
);

if (result.error) {
  console.error(
    `Unable to run COX Python CLI with ${python}: ${result.error.message}`,
  );
  console.error(
    "Install Python dependencies with `python -m pip install PyYAML jsonschema typer rich` or set COX_PYTHON.",
  );
  process.exit(1);
}

process.exit(result.status ?? 1);