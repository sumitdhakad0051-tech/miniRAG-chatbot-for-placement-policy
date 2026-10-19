import fs from "fs";
import path from "path";
import { PDFParse } from "pdf-parse";

const DATA_DIR = "data";
const OUT_FILE = "store/chunks.json";
const CHUNK_SIZE = 800; 
const OVERLAP = 120;    


const NOISE = [
  /^Page \d+ of \d+$/i,
  /^Placement Policy$/i,
  /^Placement Policy\s+MNIT Jaipur$/i,
  /^MNIT Jaipur$/i,
  /^[`'"]+$/,
];

const HEADING = /^\d+\.\d+(\.\d+)*\s+[A-Za-z]/;

async function readPdfPages(file) {
  const parser = new PDFParse({ data: new Uint8Array(fs.readFileSync(file)) });
  try {
    const result = await parser.getText();
    return result.pages ?? [{ num: 1, text: result.text }];
  } finally {
    await parser.destroy();
  }
}

function toBlocks(pages, source) {
  const blocks = [];
  let current = { section: "Introduction", page: 1, lines: [] };
  for (const { num, text } of pages) {
    if (/TABLE OF CONTENTS/i.test(text)) continue;
    for (let line of text.split("\n")) {
      line = line.trim();
      if (!line || NOISE.some((r) => r.test(line))) continue;
      if (HEADING.test(line) && line.length < 80) {
        if (current.lines.length) blocks.push(current);
        current = { section: line, page: num, lines: [] };
      } else {
        current.lines.push(line);
      }
    }
  }
  if (current.lines.length) blocks.push(current);
  return blocks.map((b) => ({
    source,
    section: b.section,
    page: b.page,
    text: b.lines.join(" "),
  }));
}

function splitText(text) {
  const chunks = [];
  let start = 0;
  while (start < text.length) {
    let end = Math.min(start + CHUNK_SIZE, text.length);
    if (end < text.length) {
      const cut = text.lastIndexOf(". ", end);
      if (cut > start + CHUNK_SIZE * 0.5) end = cut + 1;
    }
    chunks.push(text.slice(start, end).trim());
    if (end >= text.length) break;
    start = end - OVERLAP;
  }
  return chunks;
}

const all = [];
const files = fs.readdirSync(DATA_DIR).filter((f) => f.toLowerCase().endsWith(".pdf"));

for (const f of files) {
  const pages = await readPdfPages(path.join(DATA_DIR, f));
  const blocks = toBlocks(pages, f);
  let count = 0;
  for (const b of blocks) {
    for (const piece of splitText(b.text)) {
      all.push({
        id: all.length,
        source: b.source,
        section: b.section,
        page: b.page,
        text: `${b.section}\n${piece}`,
      });
      count++;
    }
  }
  console.log(`${f}: ${pages.length} pages -> ${count} chunks`);
}

fs.mkdirSync("store", { recursive: true });
fs.writeFileSync(OUT_FILE, JSON.stringify(all, null, 2));
console.log(`Total ${all.length} chunks saved to ${OUT_FILE}\n`);
console.log(all.slice(0, 3));