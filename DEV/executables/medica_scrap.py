import os
import csv
import json
import hashlib
import time
from urllib.parse import urlparse
from collections import deque, defaultdict
from playwright.sync_api import sync_playwright
import networkx as nx
import matplotlib.pyplot as plt

# === CONFIG ===
START_URL = "https://www.medicafoundation.org/"
OUTPUT_ROOT = "DEV/medica_foundation"
CSV_FILE = os.path.join(OUTPUT_ROOT, "crawl_assets.csv")
COOKIE_FILE = "cookies.json"
STORAGE_FILE = "storage.json"
MAX_PAGES = 20
graph_edges = defaultdict(set)

# === HELPERS ===

def sanitize_folder_name(url):
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    folder_name = path.replace("/", "_") or "index"
    return folder_name

def is_internal_link(base_url, link_url):
    return urlparse(base_url).netloc == urlparse(link_url).netloc

def extract_internal_links(base_url, page):
    links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    return [link for link in links if is_internal_link(base_url, link)]

def extract_images_and_links(page):
    imgs = page.eval_on_selector_all("img[src]", "els => els.map(e => e.src)")
    hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    return imgs, hrefs

def save_html(folder, html):
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, os.path.basename(folder) + ".html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

def append_to_csv(csv_path, page_url, images, links):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    write_header = not os.path.exists(csv_path)
    with open(csv_path, "a", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(["Page URL", "Image SRC", "Link HREF"])
        for img in images:
            writer.writerow([page_url, img, ""])
        for href in links:
            writer.writerow([page_url, "", href])

def hash_url(url):
    return hashlib.sha256(url.encode()).hexdigest()

def draw_crawl_graph(graph_data, output_path="crawl_graph.png", max_labels=20):
    G = nx.DiGraph()
    for src, dsts in graph_data.items():
        for dst in dsts:
            G.add_edge(src, dst)

    plt.figure(figsize=(20, 15))
    pos = nx.kamada_kawai_layout(G)
    nx.draw_networkx_nodes(G, pos, node_size=50, node_color='skyblue', alpha=0.8)
    nx.draw_networkx_edges(G, pos, alpha=0.4, arrows=True)

    degrees = dict(G.degree())
    top_nodes = sorted(degrees, key=degrees.get, reverse=True)[:max_labels]
    labels = {node: node for node in top_nodes}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=6)

    plt.title("Simplified Crawl Graph")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"📊 Crawl graph saved to {output_path}")

def inject_cookies_and_save_storage(playwright):
    with open(COOKIE_FILE, "r") as f:
        cookies = json.load(f)

    browser = playwright.chromium.launch(channel="chrome", headless=False)
    context = browser.new_context()
    context.add_cookies(cookies)
    page = context.new_page()
    page.goto(START_URL)
    input("✅ If you're in and no Cloudflare block, press ENTER to save session...")

    context.storage_state(path=STORAGE_FILE)
    print(f"💾 Session saved to {STORAGE_FILE}")
    browser.close()

def crawl_site(playwright):
    visited = set()
    queue = deque([START_URL])
    browser = playwright.chromium.launch(channel="chrome", headless=False)

    # Load session if available, else inject cookies
    if os.path.exists(STORAGE_FILE):
        print("🔄 Using saved session from storage.json")
        context = browser.new_context(storage_state=STORAGE_FILE)
    else:
        print("🧪 No storage.json found. Injecting cookies.")
        inject_cookies_and_save_storage(playwright)
        context = browser.new_context(storage_state=STORAGE_FILE)

    while queue and len(visited) < MAX_PAGES:
        url = queue.popleft()
        if hash_url(url) in visited:
            continue

        try:
            print(f"[+] Visiting: {url}")
            page = context.new_page()
            page.goto(url, timeout=60000)

            try:
                page.wait_for_load_state("networkidle", timeout=60000)
            except Exception:
                print("⚠️ Network idle wait timed out, continuing anyway.")

            time.sleep(1)
            folder_name = sanitize_folder_name(url)
            folder_path = os.path.join(OUTPUT_ROOT, folder_name)

            html = page.content()
            save_html(folder_path, html)

            images, links = extract_images_and_links(page)
            append_to_csv(CSV_FILE, url, images, links)

            new_links = extract_internal_links(START_URL, page)
            for link in new_links:
                graph_edges[url].add(link)
                if hash_url(link) not in visited:
                    queue.append(link)

            visited.add(hash_url(url))
            page.close()

        except Exception as e:
            print(f"[!] Error visiting {url}: {e}")

    context.storage_state(path=STORAGE_FILE)  # Update session after crawl
    browser.close()

# === MAIN ENTRY ===

if __name__ == "__main__":
    start = time.time()

    with sync_playwright() as playwright:
        crawl_site(playwright)

    print(f"\n✅ Crawl complete. HTML in '{OUTPUT_ROOT}/', assets in '{CSV_FILE}'")
    print(f"⏱️ Total time: {time.time() - start:.2f} seconds")

    draw_crawl_graph(graph_edges, output_path=os.path.join(OUTPUT_ROOT, "crawl_graph.png"))
