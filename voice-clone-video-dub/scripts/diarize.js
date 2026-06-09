#!/usr/bin/env node
// diarize.js — sliding-window speaker clustering via resemblyzer.
//
// Why this exists: resemblyzer gives a 256-dim speaker embedding per
// 1.5s window. KMeans into 2 clusters finds the host vs guest without
// any human labeling. The first 30s almost always contains the host's
// introduction, so the cluster that wins there is the host.
//
// Why not use this as the *only* speaker source: it gets soft female
// speech wrong ~5% of the time. We use it as one of three votes
// reconciled in the SKILL.md procedure.
//
// Usage: node diarize.js <vocals.wav> <srt_path> <output_json>
//
//   vocals.wav  — Demucs-isolated vocals (16kHz mono works fine)
//   srt_path    — translated SRT, used to know each segment's midpoint
//   output_json — { "<seg_i>": "L" | "C", ... }

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

if (process.argv.length < 5) {
  console.error("Usage: node diarize.js <vocals.wav> <srt_path> <output_json>");
  process.exit(1);
}

const VOCALS = process.argv[2];
const SRT = process.argv[3];
const OUT = process.argv[4];

// We delegate the heavy lifting to a one-shot Python helper
// (resemblyzer has no Node port, and we don't want to inline 1000
// lines of audio glue). The helper is a generated file we ship
// next to this script.
const HELPER = path.join(__dirname, "_diarize_helper.py");
const cmd = `python3 - <<'PY'
import json, sys, os
sys.path.insert(0, os.path.dirname("${HELPER}"))
from _diarize_helper import run
result = run("${VOCALS}", "${SRT}")
print(json.dumps(result))
PY
`;
// Fallback: run the helper script directly with args.
// We use PYTHON_BIN if set, otherwise system python3. The venv
// that the install-deps.sh script creates sets this in its
// activation banner; if you forget, diarize will fail with
// "ModuleNotFoundError: No module named 'resemblyzer'".
const PYTHON_BIN = process.env.PYTHON_BIN || "python3";
const fallback = `${PYTHON_BIN} "${HELPER}" "${VOCALS}" "${SRT}"`;

let raw;
try {
  raw = execSync(fallback, { encoding: "utf-8", maxBuffer: 64 * 1024 * 1024 });
} catch (e) {
  console.error("diarize failed:", e.message);
  process.exit(2);
}

let parsed;
try {
  parsed = JSON.parse(raw.trim().split("\n").pop());
} catch (e) {
  console.error("could not parse diarize output:", raw.slice(-200));
  process.exit(3);
}

fs.writeFileSync(OUT, JSON.stringify(parsed, null, 2));
console.error(`wrote ${OUT} with ${Object.keys(parsed).length} entries`);
