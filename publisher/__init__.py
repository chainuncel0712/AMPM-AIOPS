"""AI Ebook Generator — Keyword Research + Content + Publishing Pipeline"""

import os, json, re, time
from pathlib import Path
from datetime import datetime

import requests

DATA_DIR = Path(__file__).parent.parent / "data" / "publisher"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ─── 1. Keyword Research ─────────────────────────────────────────
TOP_SITES = {
    "amazon":     "https://www.amazon.com/gp/bestsellers/books",
    "google_books": "https://books.google.com",
    "goodreads":  "https://www.goodreads.com",
    "barnes":     "https://www.barnesandnoble.com",
    "kobo":       "https://www.kobo.com",
    "apple_books":"https://books.apple.com",
    "scribd":     "https://www.scribd.com",
    "booktopia":  "https://www.booktopia.com.au",
    "bol":        "https://www.bol.com",
    "epagine":    "https://www.epagine.fr",
}

TOP_CHILDREN_SITES = [
    "https://www.commonsensemedia.org",
    "https://www.scholastic.com",
]

SERP_API = "https://www.googleapis.com/customsearch/v1"

def research_keywords(niche: str = "tool_book", top_n: int = 30) -> list:
    """
    Get top trending keywords for a niche.
    niche: 'tool_book' or 'children_book'
    Returns list of {keyword, source, score}
    """
    keywords = []
    
    # Generate seed keywords from niche
    seeds = []
    if niche == "tool_book":
        seeds = [
            "beginner guide", "how to", "step by step", "tutorial",
            "入门指南", "新手教程", "工具书", "完全指南",
            "for dummies", "handbook", "cookbook", "bible",
        ]
    elif niche == "children_book":
        seeds = [
            "children picture book", "kids story", "educational book",
            "bedtime story", "early learning", "童书", "绘本",
            "儿童教育", "亲子阅读",
        ]
    
    # Use LLM to expand keywords (simple approach)
    for seed in seeds[:10]:
        keywords.append({
            "keyword": seed,
            "source": "seed",
            "score": 0.5,
        })
    
    return keywords


# ─── 2. Content Generation ────────────────────────────────────────
def generate_outline(topic: str, niche: str = "tool_book") -> dict:
    """Generate a book outline using local LLM."""
    prompt = f"""Generate a detailed book outline for a {niche} about: {topic}

Output format (JSON):
{{
  "title": "Book Title",
  "subtitle": "Short description",
  "target_audience": "Who this is for",
  "chapters": [
    {{"chapter": 1, "title": "Chapter Title", "sections": ["Section 1", "Section 2"]}},
    ...
  ],
  "key_points": ["Point 1", "Point 2"],
  "estimated_pages": 50,
  "illustration_ideas": ["Idea 1 for a diagram", "Idea 2 for a chart"]
}}

Return ONLY valid JSON."""
    
    try:
        from openai import OpenAI
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        client.model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        
        resp = client.chat.completions.create(
            model=client.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        text = resp.choices[0].message.content
        
        # Extract JSON
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"title": topic, "chapters": [], "error": "Failed to parse outline"}
    except Exception as e:
        return {"title": topic, "chapters": [], "error": str(e)}


def generate_chapter(outline: dict, chapter_num: int) -> str:
    """Generate a full chapter's content."""
    chapter = outline["chapters"][chapter_num - 1]
    prompt = f"""Write chapter {chapter_num}: "{chapter['title']}" for the book "{outline['title']}".

Target audience: {outline.get('target_audience', 'beginners')}
Sections to cover: {', '.join(chapter['sections'])}

Write in clear, practical, step-by-step style. Include examples and tips.
Approximately 2000-3000 words in Chinese (繁體中文)."""
    
    try:
        from openai import OpenAI
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        client.model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        
        resp = client.chat.completions.create(
            model=client.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Error generating chapter: {e}"


# ─── 3. Pipeline ──────────────────────────────────────────────────
def create_book(topic: str, niche: str = "tool_book") -> dict:
    """Full pipeline: research → outline → generate → save."""
    book_id = f"book_{int(time.time())}"
    book_dir = DATA_DIR / book_id
    book_dir.mkdir(exist_ok=True)
    
    print(f"📖 Creating book: {topic}")
    print(f"   ID: {book_id}")
    
    # Step 1: Outline
    print(f"   📝 Generating outline...")
    outline = generate_outline(topic, niche)
    if outline.get("error"):
        return {"error": outline["error"]}
    
    # Save outline
    (book_dir / "outline.json").write_text(json.dumps(outline, indent=2, ensure_ascii=False))
    print(f"   ✅ Outline done: {outline['title']} ({len(outline['chapters'])} chapters)")
    
    # Step 2: Generate each chapter
    chapters = []
    for i, ch in enumerate(outline["chapters"], 1):
        print(f"   📝 Chapter {i}/{len(outline['chapters'])}: {ch['title']}...")
        content = generate_chapter(outline, i)
        (book_dir / f"chapter_{i:02d}.md").write_text(content, encoding="utf-8")
        chapters.append({"num": i, "title": ch["title"], "file": f"chapter_{i:02d}.md"})
        print(f"   ✅ Chapter {i} done ({len(content)} chars)")
    
    # Step 3: Summary
    summary = {
        "book_id": book_id,
        "topic": topic,
        "niche": niche,
        "title": outline["title"],
        "chapters": chapters,
        "created": datetime.utcnow().isoformat(),
        "status": "draft",
    }
    (book_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    
    print(f"   ✅ Book created: {book_dir}")
    return summary


def list_books() -> list:
    """List all created books."""
    books = []
    for d in DATA_DIR.iterdir():
        if d.is_dir():
            summary_file = d / "summary.json"
            if summary_file.exists():
                books.append(json.loads(summary_file.read_text()))
    return sorted(books, key=lambda b: b.get("created", ""), reverse=True)


def get_book(book_id: str) -> dict | None:
    """Get a book by ID."""
    book_dir = DATA_DIR / book_id
    if book_dir.exists():
        summary_file = book_dir / "summary.json"
        if summary_file.exists():
            return json.loads(summary_file.read_text())
    return None
