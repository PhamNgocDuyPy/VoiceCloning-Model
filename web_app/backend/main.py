import os
import sys

# Force eager attention for transformers to avoid SDPA returning None for attentions (fixes Viterbox)
import transformers.utils.import_utils
transformers.utils.import_utils.is_torch_sdpa_available = lambda: False

import time
import uuid
import shutil
import requests
import json
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()

from .model_manager import manager
from .utils import dub_video, concatenate_audios

app = FastAPI(title="VoiceLab Web API")

# Configure CORS so Vite frontend (port 5173) can communicate with backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUTS_DIR = os.path.join(STATIC_DIR, "outputs")

# Ensure output directory exists
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# API Models


class DubMemeRequest(BaseModel):
    text: str
    model: str
    voice: str
    video_id: str

class BenchmarkRequest(BaseModel):
    text: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    character: str
    model: str
    voice: str
    history: List[ChatMessage] = []

class ChatPairRequest(BaseModel):
    topic: str
    char_a: str
    model_a: str
    voice_a: str
    char_b: str
    model_b: str
    voice_b: str
    turns: int = 2

class ABTestRequest(BaseModel):
    text: str
    model_a: str
    voice_a: str
    model_b: str
    voice_b: str

class PronunciationItem(BaseModel):
    original: str
    replacement: str


@app.post("/api/generate")
async def generate_speech(
    text: str = Form(...),
    model: str = Form(...),
    voice: str = Form(...),
    ref_audio: Optional[UploadFile] = File(None)
):
    try:
        engine = manager.get_engine(model)
        
        # Unique output filename
        output_filename = f"{uuid.uuid4()}.wav"
        output_path = os.path.join(OUTPUTS_DIR, output_filename)
        
        # Handle reference audio for zero-shot cloning
        ref_path = None
        if ref_audio:
            temp_ref_name = f"ref_{uuid.uuid4()}_{ref_audio.filename}"
            ref_path = os.path.join(OUTPUTS_DIR, temp_ref_name)
            with open(ref_path, "wb") as buffer:
                shutil.copyfileobj(ref_audio.file, buffer)
            
            # Auto set voice_id to custom if a file is uploaded for models that support zero-shot
            if model in ["viterbox", "vieneu", "vieneu_base"] and voice != "custom":
                voice = "custom"
        
        # Run inference
        engine.generate(text=text, voice_id=voice, ref_audio_path=ref_path, output_path=output_path)
        
        # Clean up temporary reference audio if created
        if ref_path and os.path.exists(ref_path):
            try:
                os.remove(ref_path)
            except Exception as e:
                print(f"[Warn] Failed to delete temp ref file: {e}")
                
        return {"audio_url": f"/static/outputs/{output_filename}"}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))





@app.post("/api/dub-meme")
async def dub_meme_video(request: DubMemeRequest):
    try:
        # Step 1: Generate the audio
        engine = manager.get_engine(request.model)
        audio_filename = f"meme_audio_{uuid.uuid4()}.wav"
        audio_path = os.path.join(OUTPUTS_DIR, audio_filename)
        
        engine.generate(text=request.text, voice_id=request.voice, ref_audio_path=None, output_path=audio_path)
        
        # Step 2: Path of video template
        video_template_path = os.path.join(STATIC_DIR, "memes", f"{request.video_id}.mp4")
        if not os.path.exists(video_template_path):
            raise HTTPException(status_code=400, detail=f"Meme template {request.video_id} not found.")
            
        # Step 3: Run FFmpeg to merge
        output_video_filename = f"meme_dubbed_{uuid.uuid4()}.mp4"
        output_video_path = os.path.join(OUTPUTS_DIR, output_video_filename)
        
        dub_video(video_template_path, audio_path, output_video_path)
        
        # Clean up temporary audio file
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass
                
        return {"video_url": f"/static/outputs/{output_video_filename}"}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/benchmark")
async def run_benchmark(request: BenchmarkRequest):
    try:
        results = []
        
        # Model 1: Piper (Baseline)
        t_start = time.time()
        piper_filename = f"bench_piper_{uuid.uuid4()}.wav"
        piper_path = os.path.join(OUTPUTS_DIR, piper_filename)
        piper_engine = manager.get_engine("piper")
        piper_engine.generate(text=request.text, voice_id="vi_VN-25hours_single-low", ref_audio_path=None, output_path=piper_path)
        t_piper = time.time() - t_start
        
        # Calculate RTF and MOS
        import soundfile as sf
        from .utils import estimate_mos_score
        audio_len = 0.0
        if os.path.exists(piper_path):
            data, samplerate = sf.read(piper_path)
            audio_len = len(data) / samplerate
        rtf_piper = audio_len / max(t_piper, 0.001)
        mos_piper = estimate_mos_score(piper_path)
        
        results.append({
            "model": "Piper TTS",
            "type": "VITS ONNX (Baseline)",
            "latency": t_piper,
            "rtf": rtf_piper,
            "ram": "< 100 MB",
            "mos": mos_piper,
            "audio_url": f"/static/outputs/{piper_filename}"
        })
        
        # Model 2: Viterbox
        t_start = time.time()
        viterbox_filename = f"bench_viterbox_{uuid.uuid4()}.wav"
        viterbox_path = os.path.join(OUTPUTS_DIR, viterbox_filename)
        viterbox_engine = manager.get_engine("viterbox")
        viterbox_engine.generate(text=request.text, voice_id="amee", ref_audio_path=None, output_path=viterbox_path)
        t_viterbox = time.time() - t_start
        
        rtf_viterbox = audio_len / max(t_viterbox, 0.001)
        mos_viterbox = estimate_mos_score(viterbox_path)
        
        results.append({
            "model": "Viterbox TTS",
            "type": "Chatterbox Flow-matching (SOTA)",
            "latency": t_viterbox,
            "rtf": rtf_viterbox,
            "ram": "~1.5 GB",
            "mos": mos_viterbox,
            "audio_url": f"/static/outputs/{viterbox_filename}"
        })
        
        # Model 3: VieNeu-TTS
        t_start = time.time()
        vieneu_filename = f"bench_vieneu_{uuid.uuid4()}.wav"
        vieneu_path = os.path.join(OUTPUTS_DIR, vieneu_filename)
        vieneu_engine = manager.get_engine("vieneu")
        vieneu_engine.generate(text=request.text, voice_id="SonTungMTP", ref_audio_path=None, output_path=vieneu_path)
        t_vieneu = time.time() - t_start
        
        rtf_vieneu = audio_len / max(t_vieneu, 0.001)
        mos_vieneu = estimate_mos_score(vieneu_path)
        
        results.append({
            "model": "VieNeu-TTS",
            "type": "Autoregressive LLM (LoRA Custom)",
            "latency": t_vieneu,
            "rtf": rtf_vieneu,
            "ram": "~1.0 GB",
            "mos": mos_vieneu,
            "audio_url": f"/static/outputs/{vieneu_filename}"
        })
        
        return {"results": results}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat_partner(request: ChatRequest):
    try:
        gemini_key = os.getenv("GEMINI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        
        personas = {
            "SonTungMTP": "Bạn đóng vai ca sĩ Sơn Tùng MTP. Hãy trả lời cực kỳ ngắn gọn, thân mật, xưng 'anh' hoặc 'mình', gọi người dùng là 'Sky' hoặc 'bạn'. Sử dụng từ ngữ đặc sắc như 'tuyệt vời', 'Sky ơi', 'ấm áp'. Giới hạn câu trả lời dưới 30 từ, viết bằng tiếng Việt tự nhiên.",
            "do_mixi": "Bạn đóng vai Độ Mixi (Tộc trưởng). Hãy trả lời bỗ bã, vui vẻ, xưng 'tôi' gọi 'ông/bạn/anh em', dùng từ ngữ gần gũi, mộc mạc kiểu 'nhá', 'nhỉ', 'anh em'. Giới hạn câu trả lời dưới 30 từ, viết bằng tiếng Việt tự nhiên.",
            "barack_obama": "You are Barack Obama. Speak in a calm, inspirational, and presidential tone. Respond in Vietnamese, keeping it under 25 words.",
            "donald_trump": "You are Donald Trump. Speak in a highly energetic, boastful, and confident tone. Respond in Vietnamese, keeping it under 20 words.",
            "tran_thanh": "Bạn đóng vai MC Trấn Thành. Trả lời đầy cảm xúc, nghệ sĩ, hay nói triết lý nhẹ nhàng và thân mật. Giới hạn câu trả lời dưới 30 từ, viết bằng tiếng Việt."
        }
        
        system_instruction = personas.get(request.character, "Bạn là trợ lý AI thân thiện. Hãy trả lời rất ngắn gọn dưới 30 từ bằng tiếng Việt.")
        response_text = ""
        
        # --- Try Groq API first ---
        if groq_key and groq_key != "YOUR_GROQ_API_KEY_HERE":
            try:
                messages = [{"role": "system", "content": system_instruction}]
                for msg in request.history:
                    messages.append({"role": msg.role, "content": msg.content})
                messages.append({"role": "user", "content": request.message})
                
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {groq_key}"
                }
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": messages,
                    "max_tokens": 150,
                    "temperature": 0.7
                }
                
                res = requests.post(url, headers=headers, json=payload, timeout=10)
                if res.status_code == 200:
                    res_data = res.json()
                    response_text = res_data["choices"][0]["message"]["content"].strip()
                    print(f"[Groq] Response generated successfully.")
                else:
                    print(f"[Groq API Error] {res.status_code}: {res.text}")
                    raise Exception(f"Groq API returned code {res.status_code}")
            except Exception as groq_ex:
                print(f"[Groq Error] {groq_ex}. Trying Gemini fallback...")
                response_text = ""

        # --- Fallback to Gemini API ---
        if not response_text and gemini_key and gemini_key != "YOUR_GEMINI_API_KEY_HERE":
            try:
                contents = []
                for msg in request.history:
                    contents.append({
                        "role": "user" if msg.role == "user" else "model",
                        "parts": [{"text": msg.content}]
                    })
                contents.append({
                    "role": "user",
                    "parts": [{"text": f"[Chỉ thị hệ thống: {system_instruction}]\nTin nhắn mới: {request.message}"}]
                })
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                headers = {"Content-Type": "application/json"}
                payload = {"contents": contents}
                
                res = requests.post(url, headers=headers, json=payload, timeout=10)
                if res.status_code == 200:
                    res_data = res.json()
                    response_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                else:
                    print(f"[Gemini API Error] {res.status_code}: {res.text}")
                    raise Exception(f"Gemini API returned code {res.status_code}")
            except Exception as gem_ex:
                print(f"[Gemini Error] {gem_ex}. Using simulated replies...")
                response_text = ""
                
        # --- Final fallback: simulated replies ---
        if not response_text:
            simulated_replies = {
                "SonTungMTP": "Sky ơi! Cảm ơn bạn rất nhiều vì đã luôn đồng hành cùng anh. Sky là động lực lớn nhất của anh đấy nha! Chúc Sky một ngày tuyệt vời nhé!",
                "do_mixi": "Chào ông nhé! Hôm nay thế nào rồi anh em? Có gì vui không kể tôi nghe xem nào, mọi việc vẫn ổn áp chứ hả?",
                "barack_obama": "Xin chào. Tôi rất vui được trò chuyện với bạn. Hãy luôn tin tưởng rằng chúng ta có thể làm nên sự khác biệt cùng nhau.",
                "donald_trump": "Chào bạn! Mọi người đang nói rằng cuộc trò chuyện này là tuyệt vời nhất, chưa từng có ai làm được như thế này luôn. Tin tôi đi!",
                "tran_thanh": "Chào bạn nha, Thành rất vui khi được trò chuyện cùng bạn. Cuộc đời này có rất nhiều câu chuyện xúc động, hãy trân trọng nó nhé!"
            }
            response_text = simulated_replies.get(request.character, "Chào bạn nhé! Tôi là trợ lý ảo sẵn sàng trò chuyện cùng bạn.")
            
        engine = manager.get_engine(request.model)
        output_filename = f"chat_{uuid.uuid4()}.wav"
        output_path = os.path.join(OUTPUTS_DIR, output_filename)
        
        engine.generate(text=response_text, voice_id=request.voice, ref_audio_path=None, output_path=output_path)
        
        # --- Lưu lịch sử chat ---
        try:
            from datetime import datetime
            history_file = os.path.join(STATIC_DIR, "chat_history.json")
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "character": request.character,
                "user_message": request.message,
                "bot_response": response_text,
                "audio_url": f"/static/outputs/{output_filename}"
            }
            
            # Đọc lịch sử cũ nếu có
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    try:
                        logs = json.load(f)
                    except:
                        logs = []
            else:
                logs = []
                
            # Thêm tin nhắn mới và lưu lại
            logs.append(log_entry)
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as log_ex:
            print(f"[Warning] Failed to save chat history: {log_ex}")
            
        return {
            "text": response_text,
            "audio_url": f"/static/outputs/{output_filename}"
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat_pair")
async def chat_pair(request: ChatPairRequest):
    try:
        gemini_key = os.getenv("GEMINI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        
        if (not gemini_key or gemini_key == "YOUR_GEMINI_API_KEY_HERE") and \
           (not groq_key or groq_key == "YOUR_GROQ_API_KEY_HERE"):
            raise HTTPException(status_code=500, detail="Chưa cấu hình GEMINI_API_KEY hoặc GROQ_API_KEY ở server.")
            
        prompt = f"""
        Bạn là đạo diễn kịch bản. Hãy viết một cuộc hội thoại ngắn gọn giữa hai nhân vật nổi tiếng sau đây:
        Nhân vật A: {request.char_a}
        Nhân vật B: {request.char_b}
        
        Chủ đề cuộc trò chuyện: {request.topic}
        Số lượt thoại: Mỗi nhân vật nói đúng {request.turns} câu (Tổng cộng {request.turns * 2} câu), xen kẽ nhau. Bắt đầu bằng Nhân vật A.
        Mỗi câu thoại phải ngắn gọn (dưới 25 từ), đúng phong cách của nhân vật, hài hước và tự nhiên bằng tiếng Việt.
        
        Trả về kết quả chuẩn định dạng JSON array (không markdown, không thêm chữ khác):
        [
            {{"character": "{request.char_a}", "text": "câu thoại 1..."}},
            {{"character": "{request.char_b}", "text": "câu thoại 2..."}},
            ...
        ]
        """
        
        res_text = ""
        
        # --- Try Groq first ---
        if groq_key and groq_key != "YOUR_GROQ_API_KEY_HERE":
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {groq_key}"
                }
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.7
                }
                
                res = requests.post(url, headers=headers, json=payload, timeout=15)
                if res.status_code == 200:
                    res_text = res.json()["choices"][0]["message"]["content"].strip()
                    print("[Chat Pair] Groq succeeded.")
                else:
                    raise Exception(f"Groq returned {res.status_code}")
            except Exception as groq_ex:
                print(f"[Chat Pair Groq Error] {groq_ex}. Trying Gemini...")
                res_text = ""
                
        # --- Fallback to Gemini ---
        if not res_text and gemini_key and gemini_key != "YOUR_GEMINI_API_KEY_HERE":
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                headers = {"Content-Type": "application/json"}
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                
                res = requests.post(url, headers=headers, json=payload, timeout=15)
                if res.status_code == 200:
                    res_text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                else:
                    raise Exception(f"Gemini returned {res.status_code}")
            except Exception as gem_ex:
                print(f"[Chat Pair Gemini Error] {gem_ex}")
                raise HTTPException(status_code=500, detail="Cả Groq và Gemini đều thất bại.")
        
        if not res_text:
            raise HTTPException(status_code=500, detail="Không thể sinh kịch bản hội thoại từ bất kỳ LLM nào.")
            
        # Parse JSON
        import re
        json_match = re.search(r'\[.*\]', res_text, re.DOTALL)
        if json_match:
            script_data = json.loads(json_match.group(0))
        else:
            raise Exception("LLM API không trả về đúng định dạng JSON array.")
            
        # Synthesize voices
        results = []
        for line in script_data:
            char_name = line.get("character")
            text_to_speak = line.get("text")
            
            if char_name == request.char_a:
                engine = manager.get_engine(request.model_a)
                voice_id = request.voice_a
            else:
                engine = manager.get_engine(request.model_b)
                voice_id = request.voice_b
                
            temp_name = f"chatpair_{uuid.uuid4()}.wav"
            temp_path = os.path.join(OUTPUTS_DIR, temp_name)
            
            engine.generate(text=text_to_speak, voice_id=voice_id, ref_audio_path=None, output_path=temp_path)
            
            results.append({
                "character": char_name,
                "text": text_to_speak,
                "audio_url": f"/static/outputs/{temp_name}"
            })
            
        return {"dialogue": results}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ab-test")
async def run_ab_test(
    text: str = Form(...),
    model_a: str = Form(...),
    voice_a: str = Form(...),
    model_b: str = Form(...),
    voice_b: str = Form(...),
    ref_audio_a: UploadFile = File(None),
    ref_audio_b: UploadFile = File(None)
):
    try:
        path_ref_a = None
        if ref_audio_a:
            path_ref_a = os.path.join(OUTPUTS_DIR, f"ref_a_{uuid.uuid4()}.wav")
            with open(path_ref_a, "wb") as f:
                shutil.copyfileobj(ref_audio_a.file, f)
            if model_a in ["viterbox", "vieneu", "vieneu_base"] and voice_a != "custom":
                voice_a = "custom"
                
        path_ref_b = None
        if ref_audio_b:
            path_ref_b = os.path.join(OUTPUTS_DIR, f"ref_b_{uuid.uuid4()}.wav")
            with open(path_ref_b, "wb") as f:
                shutil.copyfileobj(ref_audio_b.file, f)
            if model_b in ["viterbox", "vieneu", "vieneu_base"] and voice_b != "custom":
                voice_b = "custom"

        # Generate Sample A
        engine_a = manager.get_engine(model_a)
        filename_a = f"ab_sample_A_{uuid.uuid4()}.wav"
        path_a = os.path.join(OUTPUTS_DIR, filename_a)
        engine_a.generate(text=text, voice_id=voice_a, ref_audio_path=path_ref_a, output_path=path_a)
        
        # Generate Sample B
        engine_b = manager.get_engine(model_b)
        filename_b = f"ab_sample_B_{uuid.uuid4()}.wav"
        path_b = os.path.join(OUTPUTS_DIR, filename_b)
        engine_b.generate(text=text, voice_id=voice_b, ref_audio_path=path_ref_b, output_path=path_b)
        
        # Cleanup refs
        for p in [path_ref_a, path_ref_b]:
            if p and os.path.exists(p):
                try: os.remove(p)
                except: pass

        # Return anonymously to prevent bias
        return {
            "sample_a_url": f"/static/outputs/{filename_a}",
            "sample_b_url": f"/static/outputs/{filename_b}"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from .utils import load_pronunciation_dict, save_pronunciation_dict

@app.get("/api/pronunciation")
async def get_pronunciation_dict():
    try:
        pdict = load_pronunciation_dict()
        items = [{"original": k, "replacement": v} for k, v in pdict.items()]
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pronunciation")
async def add_pronunciation_item(item: PronunciationItem):
    try:
        pdict = load_pronunciation_dict()
        pdict[item.original] = item.replacement
        save_pronunciation_dict(pdict)
        return {"message": "Success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/pronunciation/{word}")
async def delete_pronunciation_item(word: str):
    try:
        pdict = load_pronunciation_dict()
        if word in pdict:
            del pdict[word]
            save_pronunciation_dict(pdict)
        return {"message": "Success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve React build (dist/) if it exists, otherwise return instructions JSON
DIST_DIR = os.path.join(FRONTEND_DIR, "dist")
if os.path.exists(DIST_DIR):
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="frontend")
else:
    @app.get("/")
    async def read_index():
        return JSONResponse({
            "message": "FastAPI backend running. Please build the React app (npm run build in web_app/frontend) or run Vite dev server on http://localhost:5173"
        })
