# 🎙️ VoiceLab: Nền Tảng Giả Lập và Nhân Bản Giọng Nói Tiếng Việt

VoiceLab là một ứng dụng Web tích hợp (Full-stack) được thiết kế cho việc tổng hợp, so sánh hiệu năng và nhân bản giọng nói tiếng Việt tức thì (Zero-shot Voice Cloning) bằng cách sử dụng các mô hình học sâu (Deep Learning) hiện đại nhất.

---

## ✨ Các Tính Năng Chính

1. **Speech Synthesis (Tổng hợp giọng nói đa mô hình):**
   - **Piper TTS (VITS):** Giọng đọc siêu nhanh, chạy mượt mà trên CPU với 3 giọng chuẩn.
   - **VieNeu-TTS (LoRA Fine-tuned):** Tái tạo âm điệu đặc sắc (như Sơn Tùng MTP) bằng kỹ thuật tinh chỉnh tham số hạng thấp.
   - **VieNeu-TTS (Base):** Hỗ trợ 7 giọng mẫu chuẩn vùng miền và tính năng Zero-shot cloning tải lên trực tiếp.
   - **Viterbox (Flow-matching):** Sinh âm thanh trung thực cao (24kHz) với 5 giọng mồi nổi tiếng (Amee, Độ Mixi, Trấn Thành, Obama, Trump) và tùy chọn upload ghi âm trực tiếp.

2. **Meme Dubbing Studio (Lồng tiếng video):**
   - Chọn mẫu video meme có sẵn, nhập phụ đề và tự động lồng tiếng khớp thời gian bằng mô hình AI mong muốn.

3. **Model Benchmark Studio (So sánh hiệu năng):**
   - Đo lường và vẽ biểu đồ so sánh song song giữa các mô hình về: **Độ trễ sinh âm thanh (Latency)**, **Hệ số xử lý thời gian thực (RTF)**, **Dung lượng RAM tiêu thụ**, và điểm đánh giá **MOS**.

4. **A/B Blind Test (Thử nghiệm mù):**
   - Trình nghe ngẫu nhiên ẩn nhãn mô hình giúp đánh giá chất lượng giọng nói một cách khách quan nhất.

5. **Pronunciation Dictionary (Từ điển phát âm):**
   - Giao diện CRUD quản lý các quy tắc thay thế từ ngữ viết tắt hoặc phát âm sai trước khi đưa vào mô hình TTS.

6. **AI Chat Partner (Trò chuyện thông minh):**
   - **Chế độ 1 AI:** Chat thoại trực tiếp với các nhân vật giả lập.
   - **Chế độ 2 AI (Đạo diễn kịch bản):** Xem và nghe 2 nhân vật AI đối thoại trực tiếp theo chủ đề tự chọn.
   - **Hệ thống Fallback 3 tầng:** Tự động chuyển đổi thông minh giữa Gemini 2.5 Flash → Groq (Llama 3.3) → Câu trả lời dự phòng.

---

## 🛠️ Kiến Trúc Dự Án

- **Backend:** FastAPI (Python), quản lý mô hình (Lazy loading, GC & CUDA cache empty để tối ưu bộ nhớ), xử lý API hội thoại và xử lý âm thanh (FFmpeg, gTTS, soundfile).
- **Frontend:** React, Vite, Tailwind CSS với thiết kế **3D Glassmorphism Premium** hiện đại, mượt mà.

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Ứng Dụng

### 1. Chuẩn bị môi trường & Cài đặt thư viện
Yêu cầu Python 3.10+ và Node.js 18+.

```bash
# Cài đặt thư viện Backend
pip install -r web_app/requirements.txt

# Cài đặt thư viện Frontend
cd web_app/frontend
npm install
cd ../..
```

### 2. Thiết lập cấu hình API
Tạo file `.env` ở thư mục gốc (tham khảo [.env.example](.env.example)):
```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GROQ_API_KEY=YOUR_GROQ_API_KEY
```

### 3. Khởi tạo tài nguyên mẫu (Giọng mồi và video meme)
Chạy script để tải/tạo các file video meme và file giọng nói mẫu ban đầu:
```bash
python -m web_app.backend.setup_assets
```

### 4. Chạy ứng dụng
Khởi động cả server Backend (FastAPI) và Frontend (Vite) chỉ bằng một lệnh duy nhất:
```bash
python run_app.py
```
Ứng dụng sẽ tự động mở tại địa chỉ: **http://localhost:8000** (hoặc port của frontend hiển thị trên terminal).

---

## 🔬 Hướng Dẫn Huấn Luyện LoRA (Kaggle)

Tất cả các tài liệu huấn luyện được lưu trữ trong thư mục [notebooks/](notebooks/).

- **Notebook huấn luyện:** [notebooks/tts_tuning_lora.ipynb](notebooks/tts_finetuning_lora.ipynb) (Phiên bản **v3** đã sửa lỗi Sample Rate playback từ 16kHz thành 24kHz).
- **Hướng dẫn nhanh trên Kaggle T4 GPU:**
  1. Upload notebook lên Kaggle.
  2. Cấu hình dataset âm thanh mẫu của bạn (định dạng `file_name|text` trong metadata.csv).
  3. Huấn luyện khoảng **400 - 600 steps** (bão hòa cho tập dữ liệu ~3 giờ).
  4. Tải LoRA adapter đã lưu về và giải nén đặt vào thư mục [model/](model/) ở máy local để ứng dụng tự động nhận diện giọng LoRA mới.
