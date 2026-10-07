# Premiere TextFX Library V0.1

Prototype UXP panel cho Adobe Premiere Pro, giao diện thư viện text template kiểu CapCut.

## Yêu cầu
- Adobe Premiere Pro 25.6 trở lên.
- Adobe UXP Developer Tool.
- Bật developer mode của plugin trong Premiere.

## Cài thử
1. Mở Adobe UXP Developer Tool.
2. Add Plugin và trỏ tới `manifest.json`.
3. Load plugin.
4. Trong Premiere mở `Window > UXP Plugins > TextFX Library`.
5. Bấm **Tải** ở card để mở nguồn MOGRT.
6. Tải file .mogrt về máy.
7. Bấm **Gán** hoặc chọn một thư mục MOGRT để tool dò theo tên.
8. Đặt playhead, chọn V1-V6 và bấm **Chèn**.

## 10 mẫu đã cấu hình
Kick Fall Headline; Double Headline Blocks; Cartoon Dust; Colorful Playful Splash; Two-line Animated Title; Luminescent Gradient; Quick Bold; Film Glitch; Animated Cluster; Colorful Glitch.

## V0.1 đã có
- UI thư viện dạng card tương tự CapCut.
- Search và category.
- 10 nguồn mẫu.
- Persistent mapping tới file .mogrt local.
- Quét thư mục và auto-map theo tên.
- Chèn MOGRT tại playhead bằng Premiere UXP.
- Chọn video track V1-V6.

## Chưa có
- Preview video động.
- Tự sửa text bên trong MOGRT sau khi chèn.
- Batch apply cho subtitle.
- AI tự chọn mẫu theo nội dung.

Không nhúng trực tiếp file MOGRT bên thứ ba vào repo để tránh vấn đề phân phối lại tài nguyên có license.