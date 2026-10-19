import { ask } from "./rag.js";

const question = process.argv.slice(2).join(" ");
if (!question) {
  console.log('Usage: node src/ask.js "your question"');
  process.exit(1);
}

const { answer, sources } = await ask(question);
console.log("\nAnswer:\n" + answer);
console.log("\nSources:");
sources.forEach((s, i) =>
  console.log(`${i + 1}. ${s.section} (page ${s.page}) score=${s.score.toFixed(3)}`)
);