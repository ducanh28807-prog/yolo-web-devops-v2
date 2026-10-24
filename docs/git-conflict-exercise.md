# Báo Cáo Thực Hành Giải Quyết Xung Đột Git (Merge Conflict Exercise)

## 1. Mục Tiêu
- Thực hành tạo và xử lý xung đột nội dung (content conflict) trên Git theo yêu cầu Lab Train Week 1.
- Hiểu cấu trúc các cờ đánh dấu xung đột (`<<<<<<<`, `=======`, `>>>>>>>`) và quy trình hoàn tất commit merge.

## 2. Kịch Bản Tạo Xung Đột
- **Tập tin bị xung đột**: `docs/environment.md`
- **Nhánh A (`feature/update-specs-a`)**: Bổ sung dòng thông số bộ nhớ:
  `- **Memory**: 8GB allocated for VM`
  *(Nhánh này đã được merge vào `main` qua Pull Request #3)*.
- **Nhánh B (`feature/update-specs-b`)**: Khởi tạo từ `main` cũ, sửa cùng vị trí thành:
  `- **Memory**: 16GB Total Host RAM`
- Khi thực hiện gộp `origin/main` vào nhánh B (`git merge origin/main`), Git dừng lại với thông báo:
  `CONFLICT (content): Merge conflict in docs/environment.md`

## 3. Cách Giải Quyết Xung Đột
- **Phân tích**: Cả hai thông số đều có giá trị thực tế (16GB RAM của máy vật lý và 8GB cấp phát cho máy ảo Ubuntu).
- **Phương án lựa chọn**: Kết hợp cả hai dữ liệu thành một dòng hoàn chỉnh, xóa bỏ hoàn toàn các ký hiệu đánh dấu xung đột:
  `- **Memory**: 16GB Host RAM (8GB allocated for VM)`

## 4. Các Lệnh Đã Thực Hiện Và Kết Quả
1. `git status` -> Xác định trạng thái `both modified: docs/environment.md`.
2. Chỉnh sửa nội dung file `docs/environment.md` về phiên bản thống nhất.
3. `git add docs/environment.md` -> Đưa file đã sửa vào staging area để đánh dấu xung đột đã xử lý.
4. `git commit -m "fix(docs): resolve merge conflict in environment specs"` -> Hoàn tất commit merge.
5. Kiểm tra lại bằng `git status` -> Working tree sạch, nhánh trở về trạng thái bình thường.
