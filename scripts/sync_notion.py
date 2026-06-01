#!/usr/bin/env python3
"""
Sync published posts from a Notion database into Jekyll `_posts/`.

Environment variables:
  NOTION_TOKEN   - Notion internal integration token (secret)
  NOTION_DB_ID   - Target database id (secret)

Expected Notion database properties:
  Title    (title)            -> post title
  Slug     (rich_text)        -> URL slug (optional; derived from title if blank)
  Date     (date)             -> publish date (defaults to today if blank)
  Published(checkbox)         -> only True rows are synced
  Tags     (multi_select)     -> optional tags
  Summary  (rich_text)        -> optional excerpt/description

Usage:
  python scripts/sync_notion.py
"""
from __future__ import annotations

import os
import sys
import pathlib
import hashlib
import urllib.request
import urllib.parse
from datetime import date, datetime

from notion_client import Client
from slugify import slugify

POSTS_DIR = pathlib.Path(__file__).resolve().parent.parent / "_posts"
ASSETS_IMG_DIR = pathlib.Path(__file__).resolve().parent.parent / "assets" / "images"
IMG_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif")


# --------------------------------------------------------------------------- #
# Image download
# --------------------------------------------------------------------------- #
def download_image(url: str, slug: str, used_images: set) -> str:
    """Download a Notion-hosted image into assets/images/<slug>/ and return a
    Liquid-wrapped, baseurl-aware path. Filenames are derived from the URL path
    hash (Notion signed URLs vary only in their query string), so re-running the
    sync reuses the existing file instead of re-downloading."""
    parsed = urllib.parse.urlparse(url)
    h = hashlib.sha1(parsed.path.encode("utf-8")).hexdigest()[:12]
    ext = pathlib.Path(parsed.path).suffix.lower()
    if ext not in IMG_EXTS:
        ext = ".png"
    dest_dir = ASSETS_IMG_DIR / slug
    dest = dest_dir / f"{h}{ext}"
    rel = f"/assets/images/{slug}/{h}{ext}"
    used_images.add(dest.resolve())
    if not dest.exists():
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(url, headers={"User-Agent": "notion-blog-sync"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            dest.write_bytes(data)
            print(f"    image: {rel} ({len(data)//1024} KB)")
        except Exception as e:  # noqa: BLE001
            print(f"    WARN: image download failed ({e}); keeping remote URL", file=sys.stderr)
            return url
    # Wrap in Liquid so Jekyll prepends the site baseurl at build time.
    return "{{ '" + rel + "' | relative_url }}"


# --------------------------------------------------------------------------- #
# Rich text -> markdown
# --------------------------------------------------------------------------- #
def rich_text_to_md(rich: list[dict]) -> str:
    out = []
    for r in rich:
        t = r.get("plain_text", "")
        if not t:
            continue
        ann = r.get("annotations", {})
        href = r.get("href")
        if ann.get("code"):
            t = f"`{t}`"
        if ann.get("bold"):
            t = f"**{t}**"
        if ann.get("italic"):
            t = f"*{t}*"
        if ann.get("strikethrough"):
            t = f"~~{t}~~"
        if href:
            t = f"[{t}]({href})"
        out.append(t)
    return "".join(out)


# --------------------------------------------------------------------------- #
# Block -> markdown
# --------------------------------------------------------------------------- #
def blocks_to_md(client: Client, block_id: str, slug: str, used_images: set, depth: int = 0) -> str:
    lines: list[str] = []
    numbered_idx = 0
    cursor = None
    prev_is_list = False
    prev_list_type = None
    LIST_TYPES = ("bulleted_list_item", "numbered_list_item", "to_do")
    while True:
        resp = client.blocks.children.list(block_id=block_id, start_cursor=cursor)
        for block in resp["results"]:
            btype = block["type"]
            data = block.get(btype, {})
            rich = data.get("rich_text", [])
            text = rich_text_to_md(rich)
            indent = "  " * depth
            is_list = btype in LIST_TYPES

            # Insert a blank line when transitioning between a list group and
            # a non-list block, or between two different list types (kramdown
            # needs the separation to parse them correctly).
            if is_list and prev_is_list and prev_list_type != btype:
                lines.append("")
            elif not is_list and prev_is_list:
                lines.append("")

            if btype != "numbered_list_item":
                numbered_idx = 0

            if btype == "paragraph":
                lines.append(f"{indent}{text}\n" if text else "")
            elif btype == "heading_1":
                lines.append(f"# {text}\n")
            elif btype == "heading_2":
                lines.append(f"## {text}\n")
            elif btype == "heading_3":
                lines.append(f"### {text}\n")
            elif btype == "bulleted_list_item":
                lines.append(f"{indent}- {text}")
            elif btype == "numbered_list_item":
                numbered_idx += 1
                lines.append(f"{indent}{numbered_idx}. {text}")
            elif btype == "to_do":
                checked = "x" if data.get("checked") else " "
                lines.append(f"{indent}- [{checked}] {text}")
            elif btype == "quote":
                lines.append(f"> {text}\n")
            elif btype == "callout":
                emoji = (data.get("icon") or {}).get("emoji", "")
                lines.append(f"> {emoji} {text}\n".rstrip())
            elif btype == "code":
                lang = data.get("language", "")
                lines.append(f"```{lang}\n{text}\n```\n")
            elif btype == "divider":
                lines.append("---\n")
            elif btype == "image":
                raw = data.get("file", {}).get("url") or data.get("external", {}).get("url", "")
                caption = rich_text_to_md(data.get("caption", []))
                is_notion_hosted = bool(data.get("file", {}).get("url"))
                if raw and is_notion_hosted:
                    src = download_image(raw, slug, used_images)
                else:
                    src = raw  # external URLs are stable; keep as-is
                lines.append(f"![{caption}]({src})\n")
            elif btype == "equation":
                lines.append(f"$$\n{data.get('expression','')}\n$$\n")
            else:
                if text:
                    lines.append(f"{indent}{text}\n")

            # Recurse into children (nested lists, toggles, etc.)
            if block.get("has_children") and btype not in ("child_page", "child_database"):
                child_md = blocks_to_md(client, block["id"], slug, used_images, depth + 1)
                if child_md.strip():
                    lines.append(child_md)

            prev_is_list = is_list
            prev_list_type = btype if is_list else None

        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Property helpers
# --------------------------------------------------------------------------- #
def get_plain(prop: dict) -> str:
    if not prop:
        return ""
    ptype = prop.get("type")
    if ptype == "title":
        return "".join(t["plain_text"] for t in prop["title"])
    if ptype == "rich_text":
        return "".join(t["plain_text"] for t in prop["rich_text"])
    if ptype == "date":
        d = prop.get("date")
        return d["start"] if d else ""
    if ptype == "checkbox":
        return prop["checkbox"]
    if ptype == "multi_select":
        return [o["name"] for o in prop["multi_select"]]
    return ""


def yaml_escape(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def load_dotenv(path: pathlib.Path) -> None:
    """Minimal .env loader (stdlib only). Existing env vars take precedence."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def main() -> int:
    load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")
    token = os.environ.get("NOTION_TOKEN")
    db_id = os.environ.get("NOTION_DB_ID")
    if not token or not db_id:
        print("ERROR: NOTION_TOKEN and NOTION_DB_ID must be set", file=sys.stderr)
        return 1

    client = Client(auth=token)
    POSTS_DIR.mkdir(exist_ok=True)

    # Resolve the database's first data source (Notion's 2025 data-source model:
    # databases.query was removed; queries now run against a data_source id).
    db = client.databases.retrieve(database_id=db_id)
    data_sources = db.get("data_sources") or []
    if not data_sources:
        print("ERROR: database has no data sources", file=sys.stderr)
        return 1
    ds_id = data_sources[0]["id"]
    if len(data_sources) > 1:
        print(f"Note: DB has {len(data_sources)} data sources; using '{data_sources[0]['name']}'")

    # Query only published rows
    results = []
    cursor = None
    while True:
        resp = client.data_sources.query(
            data_source_id=ds_id,
            filter={"property": "Published", "checkbox": {"equals": True}},
            start_cursor=cursor,
        )
        results.extend(resp["results"])
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    print(f"Found {len(results)} published page(s)")
    written = 0
    seen_files = set()
    used_images: set = set()

    for page in results:
        props = page["properties"]
        title = get_plain(props.get("Title")) or "Untitled"
        slug = get_plain(props.get("Slug")) or slugify(title)
        date_str = get_plain(props.get("Date"))
        tags = get_plain(props.get("Tags")) or []
        summary = get_plain(props.get("Summary"))

        if date_str:
            post_date = date_str[:10]
        else:
            post_date = date.today().isoformat()

        filename = f"{post_date}-{slug}.md"
        seen_files.add(filename)
        filepath = POSTS_DIR / filename

        body = blocks_to_md(client, page["id"], slug, used_images)

        fm = ["---", "layout: post", f"title: {yaml_escape(title)}", f"date: {post_date}"]
        if tags:
            fm.append("tags: [" + ", ".join(yaml_escape(t) for t in tags) + "]")
        if summary:
            fm.append(f"description: {yaml_escape(summary)}")
        fm.append("---")
        content = "\n".join(fm) + "\n\n" + body + "\n"

        # Only write if changed (avoids noisy commits). Normalize CRLF so the
        # comparison is stable across platforms / Python versions. Note:
        # read_text() has no `newline` kwarg before Python 3.13, so we strip
        # carriage returns manually instead.
        if filepath.exists():
            existing = filepath.read_text(encoding="utf-8").replace("\r\n", "\n")
            if existing == content:
                print(f"  unchanged: {filename}")
                continue
        filepath.write_text(content, encoding="utf-8", newline="\n")
        written += 1
        print(f"  wrote: {filename}")

    # Remove posts that are no longer published
    for existing in POSTS_DIR.glob("*.md"):
        if existing.name not in seen_files:
            existing.unlink()
            written += 1
            print(f"  removed: {existing.name}")

    # Remove downloaded images no longer referenced by any synced post
    if ASSETS_IMG_DIR.exists():
        for img in ASSETS_IMG_DIR.rglob("*"):
            if img.is_file() and img.resolve() not in used_images:
                img.unlink()
                written += 1
                print(f"  removed image: {img.relative_to(ASSETS_IMG_DIR.parent.parent)}")
        # Prune now-empty per-slug directories
        for d in sorted(ASSETS_IMG_DIR.glob("*"), reverse=True):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()

    print(f"Done. {written} change(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
