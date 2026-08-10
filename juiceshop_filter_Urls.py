from pathlib import Path

# Prefix cần giữ
PREFIX = "https://multispinous-juliann-soberly.ngrok-free.dev/"

# File chứa danh sách URL (mỗi dòng một URL)
INPUT_FILE = "urls.txt"

# File kết quả
OUTPUT_FILE = "filtered_urls.txt"


def filter_urls(input_file: str, output_file: str):
    unique_urls = set()

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()

            if not url.startswith(PREFIX):
                continue

            # Bỏ phần prefix
            path = url[len(PREFIX) :]

            # Bỏ dòng rỗng
            if path:
                unique_urls.add(path)

    # Sắp xếp cho dễ đọc
    result = sorted(unique_urls)

    with open(output_file, "w", encoding="utf-8") as f:
        for item in result:
            f.write(item + "\n")

    print(f"Đã lọc {len(result)} URL duy nhất.")
    print(f"Kết quả được lưu tại: {output_file}")


if __name__ == "__main__":
    filter_urls(INPUT_FILE, OUTPUT_FILE)
