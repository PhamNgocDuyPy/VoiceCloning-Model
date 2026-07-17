# VoiceLab: Nền Tảng Giả Lập và Nhân Bản Giọng Nói Tiếng Việt

VoiceLab là một ứng dụng Web tích hợp (Full-stack) được thiết kế cho việc tổng hợp, so sánh hiệu năng và nhân bản giọng nói tiếng Việt tức thì (Zero-shot Voice Cloning) bằng cách sử dụng các mô hình học sâu (Deep Learning) hiện đại nhất.

---

## Thành Viên Nhóm

Dưới đây là danh sách thành viên thực hiện đồ án:

| Họ và tên | MSSV | Phân công công việc |
|---|---|---|
| Phạm Như Thái Tuấn | 23120186 | Thiết kế pipeline dữ liệu, tải audio YouTube, chuẩn hóa metadata và kiểm soát chất lượng dữ liệu. |
| Lê Trung Tín | 23120371 | Xây dựng quy trình nhận dạng lời nói, diarization, phân tích dữ liệu và chia Train/Validation/Test. |
| Phan Khắc Trường | 23120386 | Fine-tune VieNeu-v2 bằng LoRA, tối ưu hyperparameters, theo dõi loss và xử lý lỗi huấn luyện. |
| Phạm Ngọc Duy | 23122025 | Thiết kế pipeline inference, đánh giá WER/CER, Speaker Similarity và phân tích các cấu hình adapter. |
| Nguyễn Thị Mỹ Kim | 23122040 | Tổng hợp báo cáo, trực quan hóa kết quả, xây dựng kịch bản triển khai ứng dụng và kiểm thử cuối. |

---

## Kiến Trúc Dự Án

* **Backend:** FastAPI (Python), quản lý mô hình (Lazy loading, GC & CUDA cache empty để tối ưu bộ nhớ), xử lý API hội thoại và xử lý âm thanh (FFmpeg, gTTS, soundfile).
* **Frontend:** React, Vite, Tailwind CSS với thiết kế Glassmorphism hiện đại, mượt mà.

---

## Hướng Dẫn Cài Đặt & Triển Khai

Ứng dụng hỗ trợ cả hai phương thức triển khai: Cài đặt thủ công (Local) và Đóng gói Container (Docker/VPS).

### Cách 1: Triển khai bằng Docker & Docker Compose (Khuyên dùng cho VPS)

Yêu cầu máy chủ đã cài đặt Docker và Docker Compose. Phương thức này tự động vá lỗi `execstack` của `onnxruntime` trên Linux và chạy kiểm thử tự động (Smoke Test) khi build.

1. **Chuẩn bị cấu hình:**
   Tạo file `.env` ở thư mục gốc và điền các khóa API của bạn (tham khảo `.env.example`):
   ```env
   GEMINI_API_KEY=YOUR_GEMINI_API_KEY
   GROQ_API_KEY=YOUR_GROQ_API_KEY
   HF_TOKEN=YOUR_HUGGING_FACE_READ_TOKEN
   ```

2. **Chạy ứng dụng:**
   Thực hiện build và khởi chạy container dưới chế độ nền (background):
   ```bash
   docker-compose up -d --build
   ```

3. **Truy cập ứng dụng:**
   Ứng dụng sẽ chạy tại địa chỉ: **http://<IP_VPS_CỦA_BẠN>:8000**

---

### Cách 2: Cài đặt thủ công (Local)

Yêu cầu Python 3.10+, Node.js 18+ và công cụ `ffmpeg` được cài đặt trong biến môi trường (PATH) hệ thống.

1. **Thiết lập Backend:**
   ```bash
   # Tạo môi trường ảo
   python -m venv venv
   source venv/bin/activate  # Trên Windows dùng: venv\Scripts\activate

   # Cài đặt thư viện phụ thuộc
   pip install -r web_app/requirements.txt
   ```

2. **Thiết lập Frontend:**
   ```bash
   cd web_app/frontend
   npm install
   cd ../..
   ```

3. **Cấu hình môi trường:**
   Tạo file `.env` ở thư mục gốc:
   ```env
   GEMINI_API_KEY=YOUR_GEMINI_API_KEY
   GROQ_API_KEY=YOUR_GROQ_API_KEY
   HF_TOKEN=YOUR_HUGGING_FACE_READ_TOKEN
   ```

4. **Khởi tạo tài nguyên mẫu (Giọng mồi và video meme):**
   ```bash
   python -m web_app.backend.setup_assets
   ```

5. **Chạy ứng dụng:**
   ```bash
   python run_app.py
   ```
   Ứng dụng sẽ khởi chạy tại địa chỉ: **http://localhost:8000**

---

## Danh Sách và Chức Năng Các Notebook

Tất cả các tài liệu nghiên cứu, tiền xử lý và huấn luyện được lưu trữ trong thư mục `notebooks/`:

1. **`datawhisperx.ipynb`:** 
   * **Chức năng:** Công cụ nhận dạng giọng nói (speech-to-text) sử dụng Faster-Whisper và phân vai người nói (diarization) cấp độ từ (word-level).
2. **`evaltts (1).ipynb`:** 
   * **Chức năng:** Notebook đánh giá chất lượng và so sánh hiệu năng. Tiến hành chạy suy luận trên 146 câu test unseen và tự động chấm điểm khách quan qua hai thước đo: WER/CER (sử dụng Whisper làm trọng tài) và Speaker Similarity (độ tương đồng giọng qua mô hình trích xuất ECAPA-TDNN).
3. **`tts_finetuning_lora.ipynb`:** 
   * **Chức năng:** Notebook huấn luyện LoRA cho VieNeu-TTS-v2 trên GPU Kaggle T4. Tích hợp các kỹ thuật tối ưu hóa phần cứng (dynamic padding, gradient accumulation, AdamW 8-bit, cosine decay scheduler) và early stopping để chống hiện tượng overfitting sớm.

