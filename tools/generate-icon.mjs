#!/usr/bin/env node
// Generates Dragoman's icon: a placeholder {•} — the part of a message that
// has to survive translation intact, which is what Dragoman's checks guard.
// No dependencies.
//   node tools/generate-icon.mjs                   -> .claude-plugin/icon.svg
//   node tools/generate-icon.mjs --preview out.svg -> the icon at 256, 64 and 32 px
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const SIZE = 256;
const COLORS = { tile: "#15171C", brace: "#F3EEE4", dot: "#D8452B" };
const STROKE = 18;

// One curly brace centred on x; dir = 1 for "{", -1 for "}".
function brace(x, dir) {
  const s = dir;
  return `M${x + 22 * s} 62C${x - 2 * s} 62 ${x} 74 ${x} 92V110C${x} 122 ${x - 10 * s} 128 ${x - 20 * s} 128`
    + `C${x - 10 * s} 128 ${x} 134 ${x} 146V164C${x} 184 ${x - 2 * s} 194 ${x + 22 * s} 194`;
}

const artwork = [
  `<rect width="${SIZE}" height="${SIZE}" rx="56" fill="${COLORS.tile}"/>`,
  ...[brace(84, 1), brace(172, -1)].map((d) =>
    `<path d="${d}" fill="none" stroke="${COLORS.brace}" stroke-width="${STROKE}" stroke-linecap="round" stroke-linejoin="round"/>`),
  `<circle cx="128" cy="128" r="20" fill="${COLORS.dot}"/>`,
].join("\n  ");

const icon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${SIZE} ${SIZE}" width="${SIZE}" height="${SIZE}">
  <title>Dragoman</title>
  ${artwork}
</svg>
`;

function preview() {
  const sizes = [256, 64, 32];
  const gap = 32;
  const width = sizes.reduce((sum, s) => sum + s + gap, gap);
  let x = gap;
  const cells = sizes.map((s) => {
    const cell = `<g transform="translate(${x} ${gap}) scale(${s / SIZE})">${artwork}</g>`;
    x += s + gap;
    return cell;
  });
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${SIZE + gap * 2}" width="${width}" height="${SIZE + gap * 2}">
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  ${cells.join("\n  ")}
</svg>
`;
}

const args = process.argv.slice(2);
const previewPath = args.includes("--preview") ? args[args.indexOf("--preview") + 1] : undefined;
if (previewPath) {
  writeFileSync(previewPath, preview());
  console.log(`wrote preview ${previewPath}`);
} else {
  const out = fileURLToPath(new URL("../.claude-plugin/icon.svg", import.meta.url));
  writeFileSync(out, icon);
  console.log(`wrote ${out}`);
}
