import os
import json
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import List

load_dotenv()
api_key = os.getenv("FIRECRAWL_API_KEY")

if not api_key:
    print("❌ Lỗi: Chưa cấu hình API Key trong file .env")
    exit()

app = FirecrawlApp(api_key=api_key)

# Định nghĩa Schema để Agent trả về dữ liệu cấu trúc
class DiscoveredLinks(BaseModel):
    links: List[str] = Field(description="Danh sách các URL tìm thấy sau khi tương tác với trang")
    actions_taken: List[str] = Field(description="Các hành động Agent đã thực hiện (click, scroll...)")

def agent_discovery_crawl(target_url):
    print(f"🤖 Đang kích hoạt AI Agent để khám phá: {target_url}")
    
    try:
        # Sử dụng Agent để thực hiện Deep Research thay vì Crawl thông thường
        # Agent sẽ tự động xử lý JS, Click các menu ẩn hoặc Scroll để load thêm
        agent_result = app.agent(
            prompt=(
                "Hãy đóng vai trò một chuyên gia thu thập dữ liệu. "
                "Truy cập vào trang web, thực hiện cuộn trang (scroll), nhấn vào các menu điều hướng "
                "và tìm tất cả các liên kết (URL) dẫn đến các bài viết, dự án hoặc tài liệu liên quan. "
                "Đặc biệt chú ý các link chỉ hiện ra sau khi tương tác."
            ),
            urls=[target_url], # Tập trung vào URL mục tiêu
            schema=DiscoveredLinks,
            model="spark-1-pro" # Dùng bản Pro để có khả năng suy luận và tương tác tốt nhất
        )

        if agent_result.success and hasattr(agent_result, 'data'):
            data = agent_result.data
            # Lấy links từ kết quả mà Agent đã "suy luận" và thu thập được
            discovered_urls = data.get('links', [])
            actions = data.get('actions_taken', [])

            print(f"⚙️ Các hành động AI đã thực hiện: {', '.join(actions)}")
            
            # Loại bỏ trùng lặp và làm sạch link
            unique_urls = sorted(list(set(discovered_urls)))

            print(f"\n✅ Agent đã hoàn tất khám phá!")
            print(f"📊 TỔNG SỐ URL AI TÌM THẤY: {len(unique_urls)}")

            filename = "agent_discovered_urls.txt"
            with open(filename, "w", encoding="utf-8") as f:
                for url in unique_urls:
                    f.write(f"{url}\n")

            print(f"📂 Danh sách đã lưu tại: {filename}")
            return unique_urls
            
        else:
            print("❌ Agent không trả về dữ liệu thành công.")
            return []

    except Exception as e:
        print(f"🚨 Lỗi hệ thống Agent: {str(e)}")
        return []

if __name__ == "__main__":
    TARGET_URL = "https://owasp.org/www-project-benchmark/"
    agent_discovery_crawl(TARGET_URL)