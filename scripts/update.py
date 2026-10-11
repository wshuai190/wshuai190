"""Refresh the auto-updated parts of README.md from https://shuaiwang.io (stdlib only).

- <!-- METRICS:START/END -->: Google Scholar line + cultivation realm, from /llms-full.txt
- <!-- NEWS:START/END -->: latest papers and news, from /feed.xml
"""
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

SITE = "https://shuaiwang.io"
README = Path(__file__).resolve().parent.parent / "README.md"
NEWS_ITEMS = 5


def fetch(path: str) -> str:
    request = urllib.request.Request(SITE + path, headers={"User-Agent": "wshuai190-profile-readme"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def metrics() -> str:
    text = fetch("/llms-full.txt")
    scholar = re.search(r"^- Google Scholar: ([\d,]+) citations, h-index (\d+), i10-index (\d+)", text, re.M)
    realm = re.search(r"^- Cultivation realm[^:]*: ([^/]+) / (\S+?);", text, re.M)
    if not scholar:
        raise SystemExit("could not find the Google Scholar line in llms-full.txt")
    citations, h_index, i10 = scholar.groups()
    line = f"📈 **{citations}** citations · h-index **{h_index}** · i10-index **{i10}** ([Google Scholar](https://scholar.google.com/citations?user=JDKYomkAAAAJ))"
    if realm:
        line += f" · 🧘 cultivation realm: **{realm.group(1).strip()} ({realm.group(2)})** ([what?]({SITE}/about/))"
    return line


def news() -> str:
    root = ET.fromstring(fetch("/feed.xml"))
    lines = []
    for item in list(root.iter("item"))[:NEWS_ITEMS]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or SITE).strip()
        date = parsedate_to_datetime(item.findtext("pubDate")).strftime("%b %Y")
        kind = "📄" if any(c.text == "publication" for c in item.findall("category")) else "📣"
        lines.append(f"- {kind} **{date}** — [{title}]({link})")
    return "\n".join(lines)


def replace(text: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:START -->).*?(<!-- {name}:END -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"missing {name} markers in README.md")
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}", text)


def main() -> None:
    text = README.read_text(encoding="utf-8")
    updated = replace(replace(text, "METRICS", metrics()), "NEWS", news())
    if updated != text:
        README.write_text(updated, encoding="utf-8")
        print("README.md updated")
    else:
        print("README.md already up to date")


if __name__ == "__main__":
    main()
