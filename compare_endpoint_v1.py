import json
from urllib.parse import urlsplit, parse_qsl, urlencode, quote


JSON_FILE = "BrowserUse/crawl_output/zap_urls_20260802_151347.json"
TXT_FILE = "Firecrawl/ngrok_endpoints.txt"

# Các query parameter được giữ lại
KEEP_QUERY_PARAMS = {
    "q",
    "name",
    "fields",
    "email",
    "id",
    "page",
    "limit",
    "offset",
    "sort",
    "order",
}

# Các endpoint luôn bỏ query
DROP_QUERY_PREFIXES = (
    "/socket.io",
)


def normalize_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip()

    if not endpoint:
        return ""

    parsed = urlsplit(endpoint)

    path = parsed.path

    # Chuẩn hóa //
    while "//" in path:
        path = path.replace("//", "/")

    # Bỏ "/" cuối (trừ root "/")
    if path != "/":
        path = path.rstrip("/")

    # socket.io luôn bỏ query
    if path.startswith(DROP_QUERY_PREFIXES):
        return path

    # Không có query
    if not parsed.query:
        return path

    # Giữ các query parameter cần thiết
    params = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k in KEEP_QUERY_PARAMS
    ]

    if not params:
        return path

    # Sắp xếp theo tên parameter
    params.sort()

    normalized = []

    for key, value in params:
        # parse_qsl đã decode:
        # %20 -> space
        # + -> space

        key = quote(key, safe="")
        value = quote(value, safe=",")

        normalized.append(f"{key}={value}")

    return f"{path}?{'&'.join(normalized)}"

def load_json(path: str) -> set[str]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        normalize_endpoint(item)
        for item in data
        if isinstance(item, str) and item.strip()
    }


def load_txt(path: str) -> set[str]:
    with open(path, "r", encoding="utf-8") as f:
        return {
            normalize_endpoint(line)
            for line in f
            if line.strip()
        }


def main():
    json_endpoints = load_json(JSON_FILE)
    txt_endpoints = load_txt(TXT_FILE)

    print("=" * 70)
    print("STATISTICS")
    print("=" * 70)
    print(f"JSON file : {len(json_endpoints)} unique endpoints")
    print(f"TXT  file : {len(txt_endpoints)} unique endpoints")
    print()

    common = json_endpoints & txt_endpoints

    if len(json_endpoints) > len(txt_endpoints):
        larger_name = "JSON"
        larger = json_endpoints
        smaller_name = "TXT"
        smaller = txt_endpoints
    elif len(txt_endpoints) > len(json_endpoints):
        larger_name = "TXT"
        larger = txt_endpoints
        smaller_name = "JSON"
        smaller = json_endpoints
    else:
        larger_name = None

    print(f"Common endpoints : {len(common)}")

    if larger_name is None:
        print("\nHai file có cùng số lượng endpoint.")
    else:
        print(
            f"\n{larger_name} contains "
            f"{len(larger) - len(smaller)} more unique endpoints."
        )

        only_in_larger = sorted(larger - smaller)
        only_in_smaller = sorted(smaller - larger)

        print("\n" + "=" * 70)
        print(f"Endpoints only in {larger_name} ({len(only_in_larger)})")
        print("=" * 70)

        for ep in only_in_larger:
            print(ep)

        print("\n" + "=" * 70)
        print(f"Endpoints only in {smaller_name} ({len(only_in_smaller)})")
        print("=" * 70)

        if only_in_smaller:
            for ep in only_in_smaller:
                print(ep)
        else:
            print("None")

    print("\n" + "=" * 70)
    print(f"Intersection ({len(common)})")
    print("=" * 70)

    for ep in sorted(common):
        print(ep)


if __name__ == "__main__":
    main()