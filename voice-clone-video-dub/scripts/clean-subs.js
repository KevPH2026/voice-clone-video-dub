#!/usr/bin/env node
// clean-subs.js — collapse YouTube incremental auto-captions to one
// segment per spoken line, rebase timestamps to 0.
//
// YouTube's "en-orig" SRT emits a mix of ~2s "growing" snapshots
// (where the line is still being captured) and ~10ms "stable"
// snapshots (which represent the final text shown on screen for a
// short instant). The stable snapshots are the truth.
//
// Algorithm:
//   1. Parse all SRT blocks into (start_ms, end_ms, text)
//   2. Classify each as stable (duration < 50ms) or growing
//   3. Keep only stable, merge consecutive identical text
//   4. For each remaining stable entry, the displayed time is
//      [prev_stable.start_ms, this_stable.start_ms]
//   5. Strip ">>" speaker-change markers
//   6. Cut to optional time window; rebase to 0
//
// Usage: node clean-subs.js <input.srt> <output.srt> [start_sec] [end_sec]

const fs = require("fs");
const path = require("path");

if (process.argv.length < 4) {
  console.error("Usage: node clean-subs.js <input.srt> <output.srt> [start_sec] [end_sec]");
  process.exit(1);
}

const INPUT = process.argv[2];
const OUTPUT = process.argv[3];
const START_SEC = process.argv[4] ? parseFloat(process.argv[4]) : null;
const END_SEC = process.argv[5] ? parseFloat(process.argv[5]) : null;

const content = fs.readFileSync(INPUT, "utf-8");
const blocks = content.split(/\n\s*\n/).filter((b) => b.trim());
const items = [];

for (const block of blocks) {
  const lines = block.split("\n").filter((l) => l.trim());
  if (lines.length < 2) continue;
  let timeIdx = -1;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes("-->")) {
      timeIdx = i;
      break;
    }
  }
  if (timeIdx < 0) continue;
  const m = lines[timeIdx].match(
    /(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})/
  );
  if (!m) continue;
  const sh = +m[1], sm = +m[2], ss = +m[3], sms = +m[4];
  const eh = +m[5], em = +m[6], es = +m[7], ems = +m[8];
  const start = sh * 3600000 + sm * 60000 + ss * 1000 + sms;
  const end = eh * 3600000 + em * 60000 + es * 1000 + ems;
  const text = lines
    .slice(timeIdx + 1)
    .join(" ")
    .replace(/>>\s*/g, "")   // strip speaker markers everywhere
    .replace(/\s+/g, " ")
    .trim();
  if (text) items.push({ start, end, text });
}

// Classify stable vs growing
const stable = items.filter((x) => x.end - x.start < 50);

// Merge consecutive duplicates
const merged = [];
for (const it of stable) {
  if (merged.length && merged[merged.length - 1].text === it.text) {
    merged[merged.length - 1].end = it.end;
  } else {
    merged.push({ ...it });
  }
}

// Derive displayed time windows: each stable entry's display is
// [prev.start, this.start]. Last entry's end is the video end.
const final = [];
for (let i = 0; i < merged.length; i++) {
  const s = merged[i].start;
  const e = i + 1 < merged.length ? merged[i + 1].start : merged[i].start + 3000;
  if (e <= s) continue;
  final.push({ start: s, end: e, text: merged[i].text });
}

// Optional window cut + rebase
let out = final;
if (START_SEC !== null) {
  const s0 = START_SEC * 1000;
  const e0 = END_SEC !== null ? END_SEC * 1000 : Infinity;
  out = final
    .filter((x) => x.end > s0 && x.start < e0)
    .map((x) => ({
      start: Math.max(0, x.start - s0),
      end: Math.min(e0 - s0, x.end - s0),
      text: x.text,
    }));
}

// Merge across sentence boundaries: a stable entry ending in
// punctuation (".?!" + optional closing quotes) starts a new segment.
function isSentenceEnd(t) {
  let s = t;
  while (s && '"\')]'.includes(s.slice(-1))) s = s.slice(0, -1);
  if (!s) return false;
  return ".?!".includes(s.slice(-1));
}

const merged2 = [];
for (const x of out) {
  if (
    merged2.length &&
    !isSentenceEnd(merged2[merged2.length - 1].text)
  ) {
    const last = merged2[merged2.length - 1];
    last.end = x.end;
    last.text += " " + x.text;
  } else {
    merged2.push({ ...x });
  }
}

// Long-line split (>90 chars), evenly distributed
const splitLong = (s, e, t, max = 90) => {
  const words = t.split(" ");
  if (words.join(" ").length <= max) return [{ start: s, end: e, text: t }];
  const chunks = [];
  let cur = [];
  let curLen = 0;
  for (const w of words) {
    if (cur.length && curLen + 1 + w.length > max) {
      chunks.push(cur.join(" "));
      cur = [w];
      curLen = w.length;
    } else {
      cur.push(w);
      curLen += (curLen ? 1 : 0) + w.length;
    }
  }
  if (cur.length) chunks.push(cur.join(" "));
  const dur = e - s;
  const n = chunks.length;
  return chunks.map((c, i) => ({
    start: s + (dur * i) / n,
    end: s + (dur * (i + 1)) / n,
    text: c,
  }));
};

const finalOut = [];
for (const x of merged2) finalOut.push(...splitLong(x.start, x.end, x.text));

// Format SRT
const fmt = (ms) => {
  ms = Math.max(0, Math.round(ms));
  const h = Math.floor(ms / 3600000);
  ms %= 3600000;
  const m = Math.floor(ms / 60000);
  ms %= 60000;
  const s = Math.floor(ms / 1000);
  const milli = ms % 1000;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")},${String(milli).padStart(3, "0")}`;
};

const srt = finalOut
  .map((x, i) => `${i + 1}\n${fmt(x.start)} --> ${fmt(x.end)}\n${x.text}\n`)
  .join("\n");
fs.writeFileSync(OUTPUT, srt, "utf-8");
console.error(`wrote ${OUTPUT} with ${finalOut.length} segments`);
