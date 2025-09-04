#!/usr/bin/env python3
# install required librabries 
# in terminal run -> pip install beatifulsoup4
# in terminal run -> python3 -u updateHTMLs.py "path of html directoy"

#!/usr/bin/env python3
#!/usr/bin/env python3

import argparse
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

SKIP_SCHEMES = ("http://", "https://", "//", "data:", "mailto:", "javascript:")
SPECIAL_PREFIXES = ("/-/",)  # paths like /-/media/... should only be base-prepended, not .html-appended

def needs_domain(url: str) -> bool:
    if not url:
        return False
    u = url.strip()
    return not u.startswith(SKIP_SCHEMES)

def normalize_base(base: str) -> str:
    if base.startswith(("http://", "https://")):
        return base.rstrip("/") + "/"
    return "https://" + base.lstrip("/").rstrip("/") + "/"

def should_treat_as_css(link_tag) -> bool:
    rels = [r.lower() for r in (link_tag.get("rel") or [])]
    if "stylesheet" in rels:
        return True
    if (link_tag.get("type") or "").lower() == "text/css":
        return True
    href = (link_tag.get("href") or "").lower()
    return href.endswith(".css")

def process_html_file(path: Path, base_url: str, remove_classes=None, dry_run: bool = False) -> bool:
    orig = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(orig, "html.parser")
    changed = False

    # Update <script src="...">
    for tag in soup.find_all("script", src=True):
        src = tag["src"].strip()
        if needs_domain(src):
            tag["src"] = urljoin(base_url, src)
            changed = True

    # Update <link href="..."> (only for CSS)
    for tag in soup.find_all("link", href=True):
        if not should_treat_as_css(tag):
            continue
        href = tag["href"].strip()
        if needs_domain(href):
            tag["href"] = urljoin(base_url, href)
            changed = True

    # Update <img src="...">
    for tag in soup.find_all("img", src=True):
        src = tag["src"].strip()
        if needs_domain(src):
            tag["src"] = urljoin(base_url, src)
            changed = True

    # Update <a href="...">
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()

        if not href:
            continue

        # Skip external schemes
        if href.startswith(SKIP_SCHEMES):
            continue

        # Special case: if starts with /-/ only prepend base
        if href.startswith(SPECIAL_PREFIXES):
            full_url = urljoin(base_url, href)
            if full_url != href:
                tag["href"] = full_url
                changed = True
            continue

        # Skip anchors and query strings
        if href.startswith("#") or href.startswith("?"):
            continue

        # Add .html to internal folder-style links
        if (
            not any(href.endswith(ext) for ext in [".html", ".htm", "/", "#"])
            and not "?" in href
            and not "#" in href
            and not "." in href.split("/")[-1]  # skip things like .pdf, .jpg, etc.
        ):
            tag["href"] = href + ".html"
            changed = True
            continue

        # If internal absolute path, prepend base
        if href.startswith("/"):
            full_url = urljoin(base_url, href)
            if full_url != href:
                tag["href"] = full_url
                changed = True

    # Remove elements by class
    if remove_classes:
        for cls in remove_classes:
            for tag in soup.find_all(attrs={"class": lambda c: c and cls in c.split()}):
                tag.decompose()
                changed = True

    if changed and not dry_run:
        path.write_text(str(soup), encoding="utf-8")

    return changed

def main():
    ap = argparse.ArgumentParser(description="Update JS/CSS/IMG sources and internal links in HTML.")
    ap.add_argument("folder", help="Folder containing HTML files")
    ap.add_argument(
        "--base",
        default="www.medicafoundation.org",
        help="Base domain or URL to prepend (default: www.medicafoundation.org)",
    )
    ap.add_argument(
        "--remove",
        help="Comma-separated list of class names to remove (e.g., footer,ads,banner)",
    )
    ap.add_argument(
        "--exts",
        default=".html,.htm",
        help="Comma-separated list of file extensions (default: .html,.htm)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and report changes without modifying files",
    )

    args = ap.parse_args()
    base_url = normalize_base(args.base)
    exts = {e.strip().lower() for e in args.exts.split(",") if e.strip()}
    remove_classes = [c.strip() for c in args.remove.split(",")] if args.remove else []

    folder = Path(args.folder)
    if not folder.is_dir():
        raise SystemExit(f"Not a directory: {folder}")

    changed_files = []
    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in exts:
            if process_html_file(path, base_url, remove_classes, dry_run=args.dry_run):
                changed_files.append(str(path))

    if args.dry_run:
        print("Dry run mode: no files were modified.")
        if changed_files:
            print("Would update the following files:")
            for f in changed_files:
                print("  ", f)
        else:
            print("No changes would be made.")
    else:
        if changed_files:
            print("Updated files:")
            for f in changed_files:
                print("  ", f)
        else:
            print("No files required updating.")

if __name__ == "__main__":
    main()
