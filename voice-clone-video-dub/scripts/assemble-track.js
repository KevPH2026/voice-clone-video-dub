#!/usr/bin/env node
// assemble-track.js — stitch per-segment WAVs into one continuous
// dub track aligned to the original timeline.
//
// Input is a manifest.jsonl with one record per segment:
//   { i, spk, text, s, e, path, duration_ms, ok }
//
// (s and e are millisecond timestamps; the legacy names s_ms/e_ms
//  also work)
//
// Output is a single 16kHz mono WAV equal to the longest segment end.
//
// We do this with ffmpeg's amix + adelay filter_complex so segments
// are placed at their SRT start times. Overlap is rare in podcast
// format but if it happens amix sums them (with normalize=0 to keep
// levels sane).
//
// Usage: node assemble-track.js <manifest.jsonl> <output.wav> [total_sec]
//   total_sec defaults to the highest e in the manifest.

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

if (process.argv.length < 4) {
  console.error("Usage: node assemble-track.js <manifest.jsonl> <output.wav> [total_sec]");
  process.exit(1);
}

const MANIFEST = process.argv[2];
const OUTPUT = process.argv[3];
const TOTAL_SEC = process.argv[4] ? parseFloat(process.argv[4]) : null;

function getMs(r, key) {
  if (r[key + "_ms"] !== undefined) return r[key + "_ms"];
  return r[key];
}

const records = fs
  .readFileSync(MANIFEST, "utf-8")
  .split("\n")
  .filter(Boolean)
  .map((l) => JSON.parse(l))
  .filter((r) => r.ok && r.path)
  .sort((a, b) => a.i - b.i);

const totalS =
  TOTAL_SEC !== null
    ? TOTAL_SEC
    : Math.max(...records.map((r) => getMs(r, "e"))) / 1000;

const inputs = [];
const filters = [];

records.forEach((r, idx) => {
  inputs.push("-i", r.path);
  const sMs = getMs(r, "s");
  const eMs = getMs(r, "e");
  const targetMs = eMs - sMs;
  if (targetMs <= 0) {
    console.error(`skipping seg ${r.i}: non-positive target ${targetMs}ms`);
    return;
  }
  const atempo = r.duration_ms / targetMs;
  // Clamp; very large atempo = chipmunk audio
  const a = Math.max(0.5, Math.min(2.0, atempo));
  filters.push(
    `[${idx}:a]atempo=${a.toFixed(3)},atrim=0:${(targetMs / 1000).toFixed(3)},` +
      `asetpts=PTS-STARTPTS,adelay=${sMs}|${sMs}[s${idx}]`
  );
});

if (!filters.length) {
  console.error("no segments to assemble");
  process.exit(1);
}

const mixInputs = filters.map((_, i) => `[s${i}]`).join("");
filters.push(
  `${mixInputs}amix=inputs=${filters.length}:duration=longest:normalize=0,` +
    `apad=whole_dur=${totalS.toFixed(3)},atrim=0:${totalS.toFixed(3)},asetpts=PTS-STARTPTS[mixout]`
);

const filterStr = filters.join(";");
const args = [
  "-y",
  ...inputs,
  "-filter_complex",
  filterStr,
  "-map",
  "[mixout]",
  "-ac",
  "1",
  "-ar",
  "16000",
  "-acodec",
  "pcm_s16le",
  OUTPUT,
];

console.error(`running ffmpeg with ${filters.length} segments...`);
const r = spawnSync("ffmpeg", args, { stdio: "inherit" });
if (r.status !== 0) {
  process.exit(r.status || 1);
}
console.error(`wrote ${OUTPUT}`);
