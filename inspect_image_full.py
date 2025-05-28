import base64
import io
from PIL import Image # Cần cài đặt: pip install Pillow
import os

def inspect_image_file_full_output(image_path: str):
    if not os.path.exists(image_path):
        print(f"Lỗi: Không tìm thấy file ảnh tại: {image_path}")
        return

    try:
        with open(image_path, "rb") as image_file:
            image_bytes_data = image_file.read()
        print(f"Đã đọc thành công file ảnh từ: {image_path}")
    except Exception as e:
        print(f"Lỗi khi đọc file ảnh {image_path}: {e}")
        return

    # 1. Dạng Bytes
    print(f"\n--- TOÀN BỘ Dữ liệu ảnh '{os.path.basename(image_path)}' dạng Bytes ---")
    # In ra toàn bộ dữ liệu bytes (LƯU Ý: CÓ THỂ RẤT DÀI VÀ KHÓ ĐỌC TRÊN CONSOLE)
    print(image_bytes_data)
    print(f"--- KẾT THÚC Dữ liệu Bytes (Tổng cộng: {len(image_bytes_data)} bytes) ---")


    # 2. Dạng Base64
    base64_encoded_data = base64.b64encode(image_bytes_data).decode('utf-8')
    
    print(f"\n--- TOÀN BỘ Dữ liệu ảnh '{os.path.basename(image_path)}' dạng Base64 ---")
    # In ra toàn bộ chuỗi base64 (LƯU Ý: SẼ CỰC KỲ DÀI TRÊN CONSOLE)
    print(base64_encoded_data)
    print(f"--- KẾT THÚC Dữ liệu Base64 (Tổng cộng: {len(base64_encoded_data)} ký tự) ---")
    
    # 3. Xác định MIME type bằng Pillow
    mime_type = "image/unknown"
    try:
        img_pil = Image.open(io.BytesIO(image_bytes_data))
        if img_pil.format and img_pil.format in Image.MIME:
            mime_type = Image.MIME[img_pil.format]
        print(f"\nMIME type của ảnh (từ Pillow): {mime_type} (Định dạng Pillow: {img_pil.format})")
    except Exception as e_pil:
        print(f"\nKhông thể xác định MIME type bằng Pillow: {e_pil}")
        ext = image_path.split('.')[-1].lower()
        if ext == "png": mime_type = "image/png"
        elif ext in ["jpg", "jpeg"]: mime_type = "image/jpeg"
        elif ext == "bmp": mime_type = "image/bmp"
        elif ext in ["tif", "tiff"]: mime_type = "image/tiff"
        print(f"MIME type của ảnh (dựa trên phần mở rộng file): {mime_type}")

if __name__ == "__main__":
    # Đảm bảo file IMG_4620.jpg nằm cùng thư mục với script này,
    # hoặc cung cấp đường dẫn đầy đủ tới file.
    image_file_to_inspect = "IMG_4620.png"  # Sử dụng trực tiếp tên file ảnh của bạn
    
    if os.path.exists(image_file_to_inspect):
        inspect_image_file_full_output(image_file_to_inspect)
    else:
        print(f"Lỗi: Không tìm thấy file '{image_file_to_inspect}'. Vui lòng đặt file ảnh vào cùng thư mục với script hoặc sửa đường dẫn.")