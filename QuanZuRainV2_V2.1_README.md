# QuanZu Rain V2.1 FAST

Bản vá tập trung vào đúng lỗi người dùng gặp khi render video mưa dài.

## Đã sửa
- **Thư mục xuất**: nút chọn output giờ dùng folder picker, không bắt chọn tên file.
- Tên file MP4 được sinh tự động từ video nguồn + thời lượng.
- **Mở thư mục output** hoạt động độc lập; hộp lỗi mới không khóa nút mở thư mục.
- Nhận diện riêng lỗi **No space left on device / disk full** và xóa partial output của lần render lỗi.
- Preflight dung lượng đĩa trước khi bắt đầu ghi video dài.
- Mặc định bật **Chuẩn hóa FAST**: encode video nguồn ngắn một lần (mặc định 1080p/24), sau đó loop bằng stream-copy cho 8–12 giờ.
- Điều này khôi phục tư duy engine QuanZu cũ: không copy nguyên bitrate 4K ~34 Mbps suốt 8–12h nếu không cần.
- Nếu tắt Chuẩn hóa FAST, tool vẫn cho copy nguồn trực tiếp nhưng sẽ ước lượng dung lượng và chặn trước nếu ổ đĩa không đủ.
- Smart brightness tiếp tục cache clip/block ngắn; sửa số block dư và kiểm tra dung lượng cache/output.
- Sửa pipeline Intel QSV để không ghi đè filter brightness/scale.

## Vì sao lần trước lỗi
Log thực tế cho thấy khoảng 65.3 GB đã được ghi ở mốc ~4h16 và FFmpeg trả error -28: **No space left on device**. Với bitrate gần 34 Mbps, 8 giờ có thể xấp xỉ 122 GB. Đây là lỗi dung lượng, không phải FFmpeg bị treo.

## Test
Source V2.1 có 13 test, gồm unit test và 2 integration test FFmpeg thực:
- normalized FAST + audio gốc + mưa + sóng + sấm
- Smart brightness + mưa + sóng + sấm

Source SHA256: `93b8c9d8c7bc01f10bfca9284cfd9fa33b6bbfc0c0a5e400044ab3e7ee18e180`
