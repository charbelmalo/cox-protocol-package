#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
if (process.argv.length === 3 && process.argv[2] === '--version') {
  console.log(JSON.parse(readFileSync(path.join(packageRoot, 'package.json'), 'utf8')).version);
  process.exit(0);
}
const python = process.env.COX_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const env = { ...process.env };
delete env.PYTHONPATH;
// Remove the caller's directory before importing dependencies or the bundled CLI.
const bootstrap = "import sys; root=sys.argv.pop(1); cwd=sys.argv.pop(1); sys.path=[root]+[p for p in sys.path if p and p!=cwd]; ";
const probe = spawnSync(python, ['-c', bootstrap + "print('.'.join(map(str,sys.version_info[:3]))); sys.exit(3) if sys.version_info < (3,9) else None; import yaml,jsonschema,typer,rich", packageRoot, process.cwd()], { env, encoding: 'utf8' });
if (probe.error || probe.status !== 0) {
  console.error(`COX needs Python 3.9+ with its dependencies in the selected interpreter: ${python}`);
  if (probe.error) console.error(probe.error.message);
  else if (probe.status === 3) console.error(`Detected Python ${probe.stdout.trim()}.`);
  else console.error('Install the Python package in a virtual environment, or install its requirements there; set COX_PYTHON to that environment’s Python executable.');
  process.exit(1);
}
const result = spawnSync(python, ['-c', bootstrap + "sys.argv[0]='cox-protocol'; import runpy; runpy.run_module('cox_protocol.cox_cli',run_name='__main__')", packageRoot, process.cwd(), ...process.argv.slice(2)], { env, stdio: 'inherit' });
if (result.error) console.error(`Could not start COX: ${result.error.message}`);
process.exit(result.status ?? 1);
