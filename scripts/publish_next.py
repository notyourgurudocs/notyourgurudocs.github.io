#!/usr/bin/env python3
"""
Not Your Guru — Blog Auto-Publisher
------------------------------------
Runs on a schedule (see .github/workflows/publish.yml).

What it does, every run:
1. Looks in /queue for the next post (alphabetical order, so name files
   001-, 002-, 003- ... to control publish order).
2. If one exists: moves it into /posts, stamps today's date into it,
   and regenerates index.html + sitemap.xml so the new post is listed
   and discoverable.
3. If the queue is empty: does nothing (safe to run on a schedule forever).

To add new posts: just drop a new HTML file into /queue with a
"<!-- meta: date=PENDING -->" line in the <head>, following the same
naming pattern (e.g. 003-your-next-post.html). Nothing else to configure.
"""

import re
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = ROOT / "queue"
POSTS_DIR = ROOT / "posts"
INDEX_FILE = ROOT / "index.html"
SITEMAP_FILE = ROOT / "sitemap.xml"
SITE_URL = "https://notyourgurudocs.github.io"

TITLE_RE = re.compile(r"<h1>(.*?)</h1>", re.DOTALL)
DESC_RE = re.compile(r'<meta name="description" content="(.*?)">')
DATE_RE = re.compile(r"<!-- meta: date=(.*?) -->")
EYEBROW_RE = re.compile(r'<div class="eyebrow">(.*?)</div>')


def publish_next_post():
    """Move the next queued post into /posts and stamp its date. Returns True if something was published."""
    queued = sorted(QUEUE_DIR.glob("*.html"))
    if not queued:
        print("No posts in queue. Nothing to publish.")
        return False

    next_post = queued[0]
    today = datetime.date.today().isoformat()

    content = next_post.read_text(encoding="utf-8")
    content = content.replace("date=PENDING", f"date={today}")

    dest = POSTS_DIR / next_post.name
    dest.write_text(content, encoding="utf-8")
    next_post.unlink()

    print(f"Published: {next_post.name} -> posts/{dest.name} (dated {today})")
    return True


def extract_meta(html_path: Path):
    text = html_path.read_text(encoding="utf-8")
    title_match = TITLE_RE.search(text)
    desc_match = DESC_RE.search(text)
    date_match = DATE_RE.search(text)
    eyebrow_match = EYEBROW_RE.search(text)

    title = re.sub(r"<.*?>", "", title_match.group(1)).strip() if title_match else html_path.stem
    desc = desc_match.group(1).strip() if desc_match else ""
    date = date_match.group(1).strip() if date_match else "2026-01-01"
    eyebrow = eyebrow_match.group(1).strip() if eyebrow_match else "Guide"

    return {
        "file": html_path.name,
        "title": title,
        "desc": desc,
        "date": date,
        "eyebrow": eyebrow,
    }


def build_index():
    posts = [extract_meta(p) for p in POSTS_DIR.glob("*.html")]
    posts.sort(key=lambda p: p["date"], reverse=True)

    cards = []
    for p in posts:
        cards.append(f'''    <div class="post-card">
      <div class="date">{p['date']} &middot; {p['eyebrow']}</div>
      <h2><a href="posts/{p['file']}">{p['title']}</a></h2>
      <p>{p['desc']}</p>
    </div>''')

    cards_html = "\n".join(cards)

    index_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Not Your Guru — Blunt Guides for Real Life</title>
<meta name="description" content="No sugarcoating relationship advice, workplace boundaries, and self-preservation guides. The blog for the Not Your Guru workbook series.">
<link rel="canonical" href="{SITE_URL}/">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>

<header class="site">
  <div class="wrap">
    <a class="brand" href="index.html">NOT YOUR GURU</a>
    <nav>
      <a href="index.html">Blog</a>
      <a href="https://www.etsy.com/shop/NotYourGuruDocs" target="_blank" rel="noopener">Shop</a>
    </nav>
  </div>
</header>

<section class="hero">
  <div class="wrap">
    <h1>Blunt guides for real life.</h1>
    <p>No sugarcoating. No corporate-speak. No "everything happens for a reason." Just clarity on relationships, workplace boundaries, and the stuff nobody hands you a script for.</p>
  </div>
</section>

<section class="post-list">
  <div class="wrap">
{cards_html}
  </div>
</section>

<footer class="site">
  <div class="wrap">
    Not Your Guru — blunt guides for real life. <a href="https://www.etsy.com/shop/NotYourGuruDocs" target="_blank" rel="noopener">Shop the workbooks on Etsy</a>
  </div>
</footer>

</body>
</html>
'''
    INDEX_FILE.write_text(index_html, encoding="utf-8")
    print(f"Regenerated index.html with {len(posts)} post(s).")
    return posts


def build_sitemap(posts):
    urls = [f"  <url><loc>{SITE_URL}/</loc></url>"]
    for p in posts:
        urls.append(f"  <url><loc>{SITE_URL}/posts/{p['file']}</loc></url>")
    urls_html = "\n".join(urls)

    sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls_html}
</urlset>
'''
    SITEMAP_FILE.write_text(sitemap, encoding="utf-8")
    print("Regenerated sitemap.xml")


if __name__ == "__main__":
    published = publish_next_post()
    posts = build_index()
    build_sitemap(posts)
    if published:
        print("DONE: new post published + site regenerated.")
    else:
        print("DONE: no new post, but index/sitemap refreshed for safety.")
