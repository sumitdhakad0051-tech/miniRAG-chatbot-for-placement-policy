import json
import re
from pathlib import Path

from pypdf import PdfReader

DATA_DIR = Path("data")
OUT_FILE = Path("store/chunks.json")
CHUNK_SIZE = 800  # ek chunk mein max characters
OVERLAP = 120     # do chunks ke beech common characters

# Faltu lines jo har page par repeat hoti hain
NOISE = [
    re.compile(r"^Page \d+ of \d+$", re.I),
    re.compile(r"^Placement Policy$", re.I),
    re.compile(r"^Placement Policy\s+MNIT Jaipur$", re.I),
    re.compile(r"^MNIT Jaipur$", re.I),
    re.compile(r"^[`'\"]+$"),
]
# Section heading jaise "5.1 Student Registration" ya "5.1.1 Eligibility..."
HEADING = re.compile(r"^\d+\.\d+(\.\d+)*\s+[A-Za-z]")


def read_pages(file: Path):
    """File se [(page_number, text), ...] nikalta hai."""
    if file.suffix.lower() == ".pdf":
        reader = PdfReader(str(file))
        return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
    return [(1, file.read_text(encoding="utf-8"))]


def to_blocks(pages, source):
    """Pages ko section-wise blocks mein todta hai aur noise hatata hai."""
    blocks = []
    current = {"section": "Introduction", "page": 1, "lines": []}
    for num, text in pages:
        if re.search(r"TABLE OF CONTENTS", text, re.I):
            continue
        for line in text.split("\n"):
            line = line.strip()
            if not line or any(r.match(line) for r in NOISE):
                continue
            if HEADING.match(line) and len(line) < 80:
                if current["lines"]:
                    blocks.append(current)
                current = {"section": line, "page": num, "lines": []}
            else:
                current["lines"].append(line)
    if current["lines"]:
        blocks.append(current)
    return [
        {
            "source": source,
            "section": b["section"],
            "page": b["page"],
            "text": " ".join(b["lines"]),
        }
        for b in blocks
    ]


def split_text(text):
    """Lambe text ko overlap ke saath chhote chunks mein todta hai."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            cut = text.rfind(". ", 0, end)
            if cut > start + CHUNK_SIZE * 0.5:
                end = cut + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = end - OVERLAP
    return chunks


def main():
    all_chunks = []
    files = sorted(f for f in DATA_DIR.iterdir() if f.suffix.lower() in {".pdf", ".txt", ".md"})

    for f in files:
        pages = read_pages(f)
        count = 0
        for b in to_blocks(pages, f.name):
            for piece in split_text(b["text"]):
                all_chunks.append(
                    {
                        "id": len(all_chunks),
                        "source": b["source"],
                        "section": b["section"],
                        "page": b["page"],
                        "text": f'{b["source"]} - {b["section"]}\n{piece}',
                    }
                )
                count += 1
        print(f"{f.name}: {len(pages)} pages -> {count} chunks")

    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text(json.dumps(all_chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Total {len(all_chunks)} chunks saved to {OUT_FILE}\n")
    for c in all_chunks[:3]:
        print(c)


if __name__ == "__main__":
    main()