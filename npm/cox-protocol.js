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

const result = spawnSync(
  python,
  ["-m", "tools.cox_cli", ...process.argv.slice(2)],
  {
    cwd: process.cwd(),
    env: {
      ...process.env,
      PYTHONPATH: pythonPath,
    },
    stdio: "inherit",
  },
);

if (result.error) {
  console.error(
    `Unable to run COX Python CLI with ${python}: ${result.error.message}`,
  );
  console.error(
    "Install Python dependencies with `python -m pip install -e .` or set COX_PYTHON.",
  );
  process.exit(1);
}

process.exit(result.status ?? 1);