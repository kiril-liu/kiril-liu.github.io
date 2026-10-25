#!/usr/bin/env python3
"""
Create a new page for the site.

Usage (run in the site root folder):
  python new.py books    "Deep Work"  [--meta "Cal Newport · ★★★★☆"]
  python new.py study    "Verilog Basics" [--meta "Verilog"]
  python new.py monthly                      (current month, e.g. 2026-10)
  python new.py monthly  "2026 November" --date 2026-11-30
  python new.py thoughts "Title"                         (empty template)
  python new.py thoughts "Title" --file my-text.txt      (fill body from a text file)

Any section accepts --file / --text to fill the body:
  blank line in the text = new paragraph.

Options:
  --date YYYY-MM-DD   use another date (default: today)
  --no-home           do not add the entry to Recent on index.html
"""
import sys, re, argparse, datetime, pathlib, html as _html

ROOT = pathlib.Path(__file__).resolve().parent
LABEL = {"books": "Books", "study": "Study", "monthly": "Monthly", "thoughts": "Thoughts"}

BODY = {
"thoughts": """      <p>…</p>""",
"books": """      <h2>One-line review</h2>
      <p>…</p>

      <h2>Key ideas</h2>
      <ul>
        <li>…</li>
      </ul>

      <blockquote>A sentence worth keeping.</blockquote>

      <h2>My thoughts</h2>
      <p>…</p>""",
"study": """      <h2>Goal</h2>
      <p>…</p>

      <h2>Notes</h2>
      <h3>Concept</h3>
      <p>…</p>

      <h2>Problems I met</h2>
      <ol>
        <li>…</li>
      </ol>""",
"monthly": """      <h2>What I did</h2><p>…</p>
      <h2>What I read</h2><p>…</p>
      <h2>What I learned</h2><p>…</p>
      <h2>Feelings</h2><p>…</p>
      <h2>Next month</h2><p>…</p>""",
}

def slugify(text, fallback):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or fallback

def insert_after(path, marker, new_text):
    t = path.read_text(encoding="utf-8")
    if marker not in t:
        sys.exit(f"Marker not found in {path.name}: {marker!r}")
    t = t.replace(marker, marker + "\n" + new_text, 1)
    path.write_text(t, encoding="utf-8")

def add_to_home(date, href, title):
    idx = ROOT / "index.html"
    line = f'        <li><span>{date}</span><a href="{href}">{title}</a></li>'
    insert_after(idx, '      <ul class="list">', line)
    # keep only the 5 newest lines in Recent
    t = idx.read_text(encoding="utf-8")
    m = re.search(r'(      <ul class="list">\n)(.*?)(\n      </ul>)', t, re.S)
    lines = m.group(2).split("\n")
    if len(lines) > 5:
        t = t[:m.start(2)] + "\n".join(lines[:5]) + t[m.end(2):]
        idx.write_text(t, encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("section", choices=["books", "study", "monthly", "thoughts"])
    ap.add_argument("title", nargs="?")
    ap.add_argument("--meta", default="")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--no-home", action="store_true")
    ap.add_argument("--text", default="")
    ap.add_argument("--file", default="")
    a = ap.parse_args()
    d = datetime.date.fromisoformat(a.date)

    sec = a.section
    if sec == "monthly":
        title = a.title or d.strftime("%Y %B")
        slug = d.strftime("%Y-%m")
        list_date = slug
    else:
        if not a.title:
            sys.exit("Please give a title.")
        title = a.title
        slug = slugify(title, a.date)
        list_date = a.date

    out = ROOT / sec / f"{slug}.html"
    if out.exists():
        sys.exit(f"{out.relative_to(ROOT)} already exists.")
    out.parent.mkdir(exist_ok=True)

    body = BODY[sec]
    raw = a.text
    if a.file:
        raw = pathlib.Path(a.file).read_text(encoding="utf-8")
    if raw.strip():
        paras = [" ".join(x.split()) for x in re.split(r"\n\s*\n", raw.strip()) if x.strip()]
        body = "\n".join(f"      <p>{_html.escape(x, quote=False)}</p>" for x in paras)

    tpl = (ROOT / "templates" / "post.html").read_text(encoding="utf-8")
    meta = f"<time>{a.date}</time>" + (f" &middot; {a.meta}" if a.meta else "")
    html = (tpl.replace("{{title}}", title).replace("{{section}}", sec)
               .replace("{{label}}", LABEL[sec]).replace("{{meta}}", meta)
               .replace("{{body}}", body))
    out.write_text(html, encoding="utf-8")

    li = f'      <li><span>{list_date}</span><a href="{sec}/{slug}.html">{title}</a></li>'
    insert_after(ROOT / f"{sec}.html", '    <ul class="list fade">', li)
    if not a.no_home:
        add_to_home(list_date, f"{sec}/{slug}.html", title)

    print(f"Created {out.relative_to(ROOT)}")
    print(f"Updated {sec}.html" + ("" if a.no_home else " and index.html"))
    print("Next: edit the new file, then git add . && git commit && git push")

main()
