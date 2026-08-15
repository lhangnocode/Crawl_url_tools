import os

def check_duplicate_links_from_file(input_filename, output_filename="danh_sach_loc.txt"):
    # Kiểm tra xem file có tồn tại không
    if not os.path.exists(input_filename):
        print(f"Lỗi: Không tìm thấy file '{input_filename}'. Vui lòng kiểm tra lại đường dẫn/tên file.")
        return

    # Đọc dữ liệu từ file
    with open(input_filename, 'r', encoding='utf-8') as file:
        # Lấy tất cả các dòng, loại bỏ khoảng trắng và các dòng trống
        lines = [line.strip() for line in file.readlines() if line.strip()]
    
    seen = set()
    duplicates = set()
    unique_links = []
    
    # Kiểm tra trùng lặp
    for line in lines:
        if line in seen:
            duplicates.add(line)
        else:
            seen.add(line)
            unique_links.append(line) # Giữ nguyên thứ tự ban đầu
            
    # In ra màn hình các link trùng lặp
    print(f"=== KẾT QUẢ KIỂM TRA TỪ FILE: {input_filename} ===")
    print("\n--- CÁC LINK TRÙNG LẶP ---")
    if duplicates:
        for dup in duplicates:
            print(f"- {dup}")
    else:
        print("Không có link nào trùng lặp.")
        
    # CHỈ GHI FILE NẾU CÓ LINK BỊ LẶP
    if duplicates:
        with open(output_filename, 'w', encoding='utf-8') as file:
            for link in unique_links:
                file.write(link + '\n')
        print(f"\n=> [Phát hiện lặp] Đã tự động lưu danh sách lọc vào file: '{output_filename}'")
    else:
        print("\n=> [Hoàn tất] File gốc không chứa link lặp, không cần tạo file mới.")


ten_file_dau_vao = 'agent_ui_links.txt'  # File đầu vào chứa danh sách link đã chuẩn hóa
ten_file_dau_ra = 'unique_URLs.txt' 

check_duplicate_links_from_file(ten_file_dau_vao, ten_file_dau_ra)