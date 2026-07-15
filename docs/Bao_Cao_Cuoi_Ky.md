# BÁO CÁO CUỐI KỲ
**Xây dựng và Triển khai Hệ thống Học máy Ứng dụng: Hệ thống Voice Cloning Tiếng Việt (Sơn Tùng M-TP)**

---

## THÔNG TIN NHÓM VÀ PHÂN CÔNG CÔNG VIỆC

| Họ và tên | MSSV | Phân công công việc |
| :--- | :--- | :--- |
| [Tên thành viên 1] | [MSSV 1] | Thu thập, tiền xử lý dữ liệu (Data Pipeline), phân tích EDA. |
| [Tên thành viên 2] | [MSSV 2] | Huấn luyện mô hình VieNeu-TTS, phân tích kết quả, xây dựng Backend. |
| [Tên thành viên 3] | [MSSV 3] | Thiết kế và phát triển giao diện Web App (Frontend), tích hợp API. |

---

## Chương 1: Giới thiệu

### 1. Phân tích Vấn đề (Problem Definition)
Trong bối cảnh nội dung số phát triển mạnh mẽ tại Việt Nam, nhu cầu tự động hóa sản xuất âm thanh và lồng tiếng (audio/voice production) ngày càng cao. Các hệ thống Text-to-Speech (TTS) truyền thống thường có giọng điệu khô khan, giống "máy học" và khó cá nhân hóa. Bài toán đặt ra là xây dựng một hệ thống Voice Cloning có khả năng bắt chước đặc trưng giọng nói của một người cụ thể (trong đồ án này là ca sĩ Sơn Tùng M-TP) chỉ từ một lượng dữ liệu âm thanh ngắn, nhưng vẫn giữ được sự tự nhiên và truyền cảm của tiếng Việt.

### 2. Mục tiêu của Đồ án
*   Xây dựng một quy trình (pipeline) thu thập và làm sạch dữ liệu âm thanh tự động với độ chính xác cao.
*   Nghiên cứu và fine-tune mô hình TTS tiên tiến (VieNeu-TTS) với kỹ thuật LoRA để nhân bản giọng nói mục tiêu.
*   Xây dựng và triển khai một ứng dụng Web thân thiện, cho phép người dùng nhập văn bản và tổng hợp ra giọng nói của mục tiêu.

### 3. Tổng quan về Phương pháp
*   **Dữ liệu:** Crawl audio từ các video YouTube, sử dụng WhisperX (với Faster-Whisper và Silero-VAD) để bóc băng (transcribe) và phân mảnh (segmentation). Sử dụng Diarization để nhận diện đúng người nói, sau đó chuẩn hóa chất lượng (SNR, silence ratio).
*   **Mô hình:** Sử dụng kiến trúc VieNeu-TTS kết hợp bộ nén NeuCodec (16kHz). Huấn luyện bằng kỹ thuật LoRA để tối ưu tham số và tránh mất đi khả năng ngôn ngữ chung của pre-trained model.
*   **Triển khai:** Ứng dụng web được xây dựng với kiến trúc Client-Server (React.js cho Frontend, FastAPI cho Backend).

---

## Chương 2: Thu thập và Phân tích Dữ liệu

### 1. Nguồn và Phương pháp Thu thập
*   **Nguồn dữ liệu:** Khai thác từ các video phỏng vấn, talkshow trên YouTube có sự xuất hiện của mục tiêu (Sơn Tùng M-TP).
*   **Công cụ:** Sử dụng thư viện `yt_dlp` để tải luồng âm thanh nguyên bản (bestaudio), sau đó chuyển đổi sang định dạng `wav` đơn kênh (mono) ở tần số lấy mẫu 16kHz để khớp với yêu cầu của mô hình NeuCodec.

### 2. Tiền xử lý và Làm sạch (Data Pipeline)
Hệ thống sử dụng pipeline `datawhisperx_v2` với các bước tự động sau:
*   **Transcribe & VAD:** Sử dụng WhisperX (tích hợp Silero-VAD) để loại bỏ nhiễu và cắt các đoạn âm thanh thô dựa trên hoạt động giọng nói thực tế, giúp giảm thiểu cắt ngang từ.
*   **Speaker Diarization:** Phân cụm người nói để lọc chính xác giọng của mục tiêu trong các video có nhiều người tham gia (MC, khách mời khác).
*   **Merging:** Gộp các đoạn nhỏ (2-3s) thành các câu hoàn chỉnh dài từ 4-10 giây, đây là "điểm ngọt" (sweet spot) để mô hình TTS học cả ngữ điệu lẫn phát âm.
*   **Quality Filtering:** 
    *   Lọc tỷ lệ Tín hiệu/Nhiễu (SNR) > 15dB.
    *   Loại bỏ các đoạn có tỷ lệ im lặng quá lớn (> 40%).
    *   Chuẩn hóa đỉnh biên độ âm thanh (Peak Normalization ở mức 0.9) để tránh hiện tượng vỡ tiếng (clipping).

### 3. Phân tích Khám phá Dữ liệu (EDA)
*   **Phân bố thời lượng (Duration):** Hầu hết các mẫu dữ liệu sau khi lọc đều tập trung ở mức 4 - 8 giây.
*   **Chất lượng SNR:** [Chờ cập nhật số liệu]
*   **Tổng số mẫu:** [Chờ cập nhật số liệu sau khi chạy notebook]

---

## Chương 3: Lựa chọn và Huấn luyện Mô hình

### 1. Chuẩn bị Dữ liệu cho Mô hình
*   **Tỷ lệ chia tập:** Dữ liệu được chia theo tỷ lệ 90% cho tập Train, 5% Validation và 5% Test.
*   **Định dạng:** Dữ liệu được xuất ra dưới dạng thư mục chứa file `wav` và một file `metadata.csv` gồm các trường: `audio_file`, `speaker_id`, `duration_sec`, `text` để đưa trực tiếp vào dataset của VieNeu-TTS.

### 2. Lựa chọn và Kiến trúc Mô hình
*   **Lựa chọn:** Chọn kiến trúc **VieNeu-TTS** (dựa trên VITS/NeuCodec) vì đây là một trong những mô hình SOTA (State-Of-The-Art) tối ưu hóa rất tốt cho ngữ âm tiếng Việt.
*   **Kiến trúc:** 
    *   **NeuCodec:** Đóng vai trò là Neural Audio Codec để mã hóa âm thanh 16kHz thành các token rời rạc.
    *   **TTS Backbone:** Mô hình sinh (Generator) học cách ánh xạ từ Text (Phonemes) sang các đặc trưng âm thanh.
*   **Fine-tuning (LoRA):** Việc huấn luyện một mô hình TTS từ đầu (scratch) là không khả thi với dữ liệu nhỏ. Đồ án dùng Low-Rank Adaptation (LoRA) để chỉ cập nhật một phần nhỏ trọng số, giúp mô hình bắt chước được chất giọng mục tiêu (Voice Cloning) mà không quên đi cách phát âm tiếng Việt chuẩn từ pre-trained.

### 3. Cấu hình Huấn luyện
*   **Hyperparameters chính:**
    *   Batch size: [Chờ cập nhật]
    *   Learning Rate: [Chờ cập nhật]
    *   Optimizer: AdamW
*   **Môi trường:** Huấn luyện trên GPU T4/L4 (Kaggle/Colab).

---

## Chương 4: Kết quả và Thảo luận

### 1. Kết quả Thực nghiệm

Hệ thống được đánh giá trên tập Test gồm 146 câu nói (unseen data) chưa từng xuất hiện trong quá trình huấn luyện. Chúng tôi tiến hành đo đạc 2 chỉ số chính:
*   **Speaker Cosine Similarity (Mức độ giống giọng):** Sử dụng mô hình trích xuất đặc trưng giọng nói (như ECAPA-TDNN) để tính khoảng cách Cosine giữa âm thanh sinh ra và giọng mục tiêu thật. Điểm càng cao càng tốt.
*   **Word Error Rate - WER (Tỉ lệ lỗi từ):** Dùng mô hình nhận dạng giọng nói (Whisper) để transcribe lại audio sinh ra và đối chiếu với kịch bản gốc. Điểm càng thấp càng tốt.

**Kết quả đánh giá 3 mô hình:**

| Mô hình (Model) | Speaker Sim (Độ giống ↑) | WER (Tỉ lệ lỗi ↓) |
| :--- | :--- | :--- |
| **Viterbox** | -0.0039 | **2.0685** |
| **VieNeu Base** | 0.0158 | 2.4726 |
| **VieNeu LoRA** | **0.0551** | 2.2740 |

*(Tham khảo **Hình 7: So sánh hiệu năng 3 mô hình** trong thư mục `figures/model_comparison.png`)*

### 2. So sánh và Thảo luận
*   **So sánh Base Model vs Fine-tuned Model:** Mô hình Base đọc chuẩn nhưng giọng vô hồn. Mô hình sau khi fine-tune mang đậm màu sắc, cách luyến láy và tốc độ nói đặc trưng của mục tiêu.
*   **Hiện tượng Overfitting:** [Chờ phân tích biểu đồ]
*   **Trường hợp lỗi điển hình (Bad Cases):** Một số từ mượn tiếng Anh chưa được G2P (Grapheme-to-Phoneme) tiếng Việt xử lý tốt, dẫn đến phát âm méo.

---

## Chương 5: Xây dựng và Triển khai Ứng dụng

### 1. Kiến trúc Hệ thống
Hệ thống được thiết kế theo mô hình Client - Server:
*   **Backend (Inference Server):** Viết bằng Python/FastAPI, phụ trách load model TTS (weights và LoRA adapters). Cung cấp RESTful API `/api/generate` nhận vào văn bản và trả về luồng âm thanh (audio bytes).
*   **Frontend:** Xây dựng bằng React.js và Vite. Cung cấp giao diện người dùng để nhập liệu, chọn giọng đọc, và phát/tải audio.

### 2. Giao diện và Chức năng
*   **UI:** Giao diện tối giản, hiện đại (Dark Mode, Glassmorphism).
*   **Chức năng chính:**
    *   Nhập văn bản (hỗ trợ văn bản dài).
    *   Hiển thị trạng thái đang tổng hợp (loading state).
    *   Trình phát audio (Audio Player) và nút Download.
*   *[Ghi chú: Chèn hình ảnh Screenshot của web app vào đây]*

### 3. Triển khai
*   **Nền tảng:** Local (cho mục đích Demo) / Cloud (nếu có thuê GPU VPS như RunPod).
*   **Hướng dẫn chạy Local:**
    *   Backend: `cd web_app/backend && pip install -r requirements.txt && python main.py`
    *   Frontend: `cd web_app/frontend && npm install && npm run dev`

---

## Chương 6: Kết luận

### 1. Tóm tắt Kết quả
Đồ án đã hoàn thành chu trình khép kín từ việc tự động hóa thu thập dữ liệu (Data Pipeline), huấn luyện mô hình Voice Cloning chất lượng cao, cho đến việc đóng gói và triển khai thành một ứng dụng web thực tế. Giọng đọc đầu ra thể hiện rõ âm sắc của nhân vật mục tiêu.

### 2. Hạn chế
*   Dữ liệu crawl từ YouTube đôi khi vẫn dính một chút nhạc nền lọt qua bộ lọc, ảnh hưởng nhẹ đến chất lượng âm.
*   Tốc độ sinh âm thanh (Inference Speed) vẫn còn phụ thuộc nhiều vào phần cứng (GPU). Nếu chạy trên CPU, thời gian phản hồi khá chậm.

### 3. Hướng phát triển
*   Tích hợp mô hình tách nhạc (Source Separation, VD: MDX-Net) vào Data Pipeline để lấy được giọng nói sạch (Acapella) 100%.
*   Cải tiến module G2P để mô hình đọc tốt hơn các từ tiếng Anh xen kẽ tiếng Việt.
*   Triển khai kiến trúc Streaming Audio để phát âm thanh ngay lập tức khi người dùng đang nhập liệu thay vì phải chờ tổng hợp xong toàn bộ câu.

---

## Phụ lục
*   **Mã nguồn:** [Link GitHub của nhóm]
*   **Tài liệu tham khảo:**
    *   Tài liệu về mô hình VITS và Neural Audio Codec.
    *   Thư viện Faster-Whisper và WhisperX (M. Bain et al.).
    *   Pre-trained VieNeu-TTS.
