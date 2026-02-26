# Hướng Dẫn Chạy Trên Linux (Ubuntu)

## 1. Yêu cầu hệ thống
- Hệ điều hành: Ubuntu 20.04/22.04 LTS hoặc mới hơn.
- Kết nối Internet.

## 2. Cài đặt

Mở terminal tại thư mục dự án và chạy lệnh sau để cấp quyền thực thi cho script cài đặt:

```bash
chmod +x setup.sh
```

Sau đó chạy script cài đặt:

```bash
./setup.sh
```

Script này sẽ:
- Cập nhật danh sách gói.
- Cài đặt Python 3, pip và venv.
- Tạo môi trường ảo (virtual environment).
- Cài đặt các thư viện cần thiết từ `requirements.txt`.

## 3. Chạy ứng dụng

Cấp quyền thực thi cho script chạy:

```bash
chmod +x run.sh
```

Chạy ứng dụng:

```bash
./run.sh
```

Ứng dụng sẽ khởi chạy tại địa chỉ: `http://0.0.0.0:5000` (bạn có thể truy cập qua trình duyệt tại `http://localhost:5000` hoặc IP máy chủ).

## 4. Dữ liệu
Dự án sử dụng MongoDB. Đảm bảo bạn đã cấu hình chuỗi kết nối chính xác trong file `.env` hoặc trong source code.

## 5. Lưu ý
- Nếu gặp lỗi thư viện, hãy kiểm tra lại `requirements.txt` và đảm bảo các phiên bản tương thích với Python trên Linux.
- Đảm bảo MongoDB đang chạy và có thể kết nối được.

## 6. Khắc phục sự cố thường gặp
Nếu bạn gặp lỗi `bash: ./setup.sh: /bin/bash^M: bad interpreter`, đó là do file script bị dính định dạng dòng của Windows (CRLF). Hãy chạy lệnh sau để sửa:
```bash
sed -i 's/\r$//' setup.sh
sed -i 's/\r$//' run.sh
```
