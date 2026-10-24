# Hướng Dẫn Đóng Góp (Contributing Guidelines)

Dự án tuân thủ nghiêm ngặt quy trình Git workflow tiêu chuẩn cho Lab Train DevOps.

## 1. Quy Tắc Nhánh (Branching Rules)
- Không commit hoặc push trực tiếp lên nhánh `main`. Mọi thay đổi bắt buộc phải qua Pull Request (PR).
- Đặt tên nhánh theo cấu trúc lowercase, dấu gạch nối:
  - `feature/<ten-tinh-nang>`: Phát triển tính năng mới (ví dụ: `feature/backend-skeleton`)
  - `fix/<ten-loi>`: Sửa lỗi (ví dụ: `fix/video-upload-validation`)
  - `docs/<noi-dung>`: Cập nhật tài liệu (ví dụ: `docs/project-setup`)

## 2. Quy Chuẩn Commit Message
- Sử dụng chuẩn Conventional Commits ngắn gọn, có ý nghĩa:
  - `feat: ...`
  - `fix: ...`
  - `docs: ...`
  - `test: ...`
  - `refactor: ...`

## 3. Quy Trình Mở Pull Request
1. Tạo nhánh từ `main` mới nhất.
2. Kiểm tra `git status` và `git diff` trước khi commit, đảm bảo không lẫn file rác hay secret.
3. Push nhánh lên GitHub và tạo PR trỏ vào `main`.
4. Tự review hoặc nhờ thành viên khác review diff trước khi nhấn merge.
