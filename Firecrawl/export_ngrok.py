import requests

# URL API nội bộ của Ngrok (Nơi chứa dữ liệu giao diện bạn đang xem)
# limit=1000 để lấy tối đa 1000 request gần nhất (Ngrok free thường chỉ lưu tầm này)
NGROK_API_URL = "http://localhost:4040/api/requests/http?limit=1000"


def export_ngrok_urls():
    print(f"📡 Đang kết nối tới Ngrok API: {NGROK_API_URL} ...")

    try:
        response = requests.get(NGROK_API_URL)

        if response.status_code == 200:
            data = response.json()
            requests_list = data.get("requests", [])

            print(f"🔍 Tìm thấy {len(requests_list)} request trong lịch sử.")

            # Dùng set để loại bỏ các URL trùng lặp
            unique_paths = set()

            for req in requests_list:
                # Lấy đường dẫn (URI) từ request
                # Cấu trúc: req['request']['uri'] -> ví dụ: /blog, /assets/main.js
                uri = req.get("request", {}).get("uri", "")
                if uri:
                    unique_paths.add(uri)

            # Sắp xếp và lưu ra file
            sorted_paths = sorted(unique_paths)
            output_file = "ngrok_crawled_paths.txt"

            with open(output_file, "w", encoding="utf-8") as f:
                f.writelines(f"{path}\n" for path in sorted_paths)

            print(f"✅ Đã xuất {len(sorted_paths)} đường dẫn duy nhất ra file: {output_file}")
            print("👉 Bạn có thể mở file này để xem cấu trúc website mà Firecrawl đã quét được.")

        else:
            print(f"❌ Lỗi khi gọi API Ngrok. Status code: {response.status_code}")

    except Exception as e:
        print(f"🚨 Lỗi: {e!s}")
        print("💡 Gợi ý: Hãy chắc chắn Ngrok đang chạy và bạn truy cập được localhost:4040")


if __name__ == "__main__":
    export_ngrok_urls()
