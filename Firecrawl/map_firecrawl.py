import json
import csv
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from firecrawl import Firecrawl
from dotenv import load_dotenv
import os

load_dotenv()

# ---------------------------------------------------------------------------
# Cấu hình
# ---------------------------------------------------------------------------
TARGET_URL = "https://firecrawl.dev"  # đổi thành site bạn muốn map
LIMIT = 5000                          # số URL tối đa muốn lấy
SEARCH = None                         # vd: "docs" -> chỉ lấy URL liên quan "docs"
SITEMAP_MODE = "include"              # "include" | "only" | "skip"

OUTPUT_DIR = Path("map_output")
OUTPUT_DIR.mkdir(exist_ok=True)
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

firecrawl = Firecrawl(api_key=os.getenv("FIRECRAWL_API_KEY"))


def run_map():
    kwargs = {"limit": LIMIT, "sitemap": SITEMAP_MODE}
    if SEARCH:
        kwargs["search"] = SEARCH

    res = firecrawl.map(url=TARGET_URL, **kwargs)
    return res


def export_results(res):
    links = res.links if hasattr(res, "links") else res.get("links", [])

    json_path = OUTPUT_DIR / f"map_urls_{RUN_ID}.json"
    csv_path = OUTPUT_DIR / f"map_urls_{RUN_ID}.csv"

    # Chuẩn hoá về dict để dễ xử lý dù SDK trả object hay dict
    normalized = []
    for link in links:
        if hasattr(link, "url"):
            normalized.append(
                {
                    "url": link.url,
                    "title": getattr(link, "title", None),
                    "description": getattr(link, "description", None),
                }
            )
        else:
            normalized.append(
                {
                    "url": link.get("url"),
                    "title": link.get("title"),
                    "description": link.get("description"),
                }
            )

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "path", "title"])
        for item in normalized:
            path = urlparse(item["url"]).path
            writer.writerow([item["url"], path, item["title"] or ""])

    print(f"[map] {len(normalized)} URL -> {json_path}, {csv_path}")
    return normalized


def main():
    print(f"Đang map {TARGET_URL} ...")
    res = run_map()
    export_results(res)


if __name__ == "__main__":
    main()