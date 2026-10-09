# QuanZu Rain V2 FAST

Tool FFmpeg chuyên tạo video mưa 8–12 giờ từ một video loop ngắn.

## Fix bottleneck 99%
Bản QuanZu cũ xử lý hàng nghìn clip ngắn, sau đó ghép video dài rồi mới xử lý audio. Khi video 4K dài 8–12 giờ, giai đoạn cuối có thể đứng ở 99% rất lâu vì toàn bộ dữ liệu đang được remux/ghi lại.

V2 thay engine:

- **Không bật độ sáng:** dùng `-stream_loop -1` trực tiếp trên video nguồn + `-c:v copy` + mix audio trong **một lệnh FFmpeg**. Không concat 3.000+ clip, không tạo file 8h tạm, không ghi video hai lần.
- **Bật độ sáng:** Smart Fast chỉ encode các mức sáng của video nguồn ngắn, sau đó tạo block stream-copy (mặc định 60 giây) và ghép khoảng 480 block cho 8 giờ thay vì ~3.000 clip 9 giây.
- Progress lấy từ `FFmpeg -progress pipe:1`, nên phần ghép cuối vẫn tăng % thật thay vì giữ 99% giả.

## Âm thanh
Ba lớp độc lập, mỗi lớp chọn file hoặc folder:

- Mưa
- Sóng biển
- Sấm

Âm lượng mỗi lớp được điều khiển bằng đường cong dB theo 9 mốc thời gian. Audio gốc của video có gain riêng. Tất cả được trộn bằng `amix` + limiter để hạn chế clipping.

## Bảng thời tiết
4 biểu đồ kéo thả:

1. Cường độ mưa (dB)
2. Sóng biển (dB)
3. Sấm (dB)
4. Độ sáng video (%)

Có preset Sleep / Natural / Storm và random theo seed.

## Render nhanh khuyến nghị
- Không cần đổi sáng: bỏ tick `Áp dụng đường cong ĐỘ SÁNG`. Đây là chế độ nhanh nhất.
- Cần đổi sáng: chọn `smart_fast`, bước sáng 1–2%, block 60 giây.
- Encoder Auto thử NVENC -> Intel QSV -> AMD AMF -> libx264 khi cần tạo cache sáng.

## FFmpeg
Tool tìm `ffmpeg.exe` / `ffprobe.exe` trong cùng thư mục trước, sau đó mới tìm PATH. Gói Windows từ GitHub Actions kèm sẵn FFmpeg/FFprobe.

Version: 2.0.0