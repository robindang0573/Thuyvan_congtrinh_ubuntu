markdown
# Web App Ôn Thi Thủy Văn Công Trình

Ứng dụng web ôn thi trắc nghiệm môn Thủy Văn Công Trình với Flask, MongoDB và Docker.

## Tính năng chính

- ✅ Đăng ký/Đăng nhập người dùng
- ✅ Thi thử với 20 câu hỏi ngẫu nhiên
- ✅ Import câu hỏi từ file Word (.docx)
- ✅ Lưu lịch sử thi và kết quả
- ✅ Thống kê kết quả bằng biểu đồ
- ✅ Quản lý câu hỏi (cho admin)
- ✅ Responsive design

## Công nghệ sử dụng

- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Frontend**: Bootstrap 5, JavaScript
- **Container**: Docker & Docker Compose
- **Thư viện**: python-docx, bcrypt, matplotlib

## Cài đặt và chạy ứng dụng
1. **Clone/Download dự án**
2. **Chạy ứng dụng bằng Docker Compose:**
   ```bash
   docker-compose up --build