import os
import subprocess
import numpy as np
import soundfile as sf

def create_voice_presets(presets_dir):
    """
    Generates voice preset files for Viterbox using Google TTS (gTTS).
    Each celebrity gets a unique Vietnamese sentence spoken by Google's TTS,
    which serves as a reference audio for Viterbox zero-shot cloning.
    
    Note: These are NOT the actual celebrity voices - they are placeholder
    reference audios. For real celebrity voice cloning, users should upload
    actual audio recordings of those celebrities via the web UI.
    """
    print("[Setup] Generating voice presets for Viterbox...")
    
    # Each voice gets a distinct Vietnamese sentence for reference
    voice_scripts = {
        "amee": "Xin chào tất cả mọi người, mình là một ca sĩ trẻ đến từ Việt Nam, rất vui được gặp các bạn.",
        "do_mixi": "Chào anh em, hôm nay chúng ta sẽ cùng nhau chơi game và nói chuyện vui vẻ nhé.",
        "barack_obama": "Xin chào các bạn, tôi rất vinh dự được nói chuyện với các bạn ngày hôm nay về tương lai.",
        "donald_trump": "Xin chào, tôi muốn nói rằng đất nước chúng ta rất tuyệt vời và sẽ còn tuyệt vời hơn nữa.",
        "tran_thanh": "Xin chào quý vị khán giả, tôi rất xúc động khi được đứng trên sân khấu này hôm nay."
    }
    
    try:
        from gtts import gTTS
        use_gtts = True
        print("  -> Using Google TTS for natural Vietnamese voice presets.")
    except ImportError:
        use_gtts = False
        print("  -> gTTS not available. Installing...")
        try:
            subprocess.run(["pip", "install", "gtts", "-q"], check=True)
            from gtts import gTTS
            use_gtts = True
            print("  -> gTTS installed successfully.")
        except Exception as e:
            print(f"  -> Failed to install gTTS: {e}. Falling back to sine wave.")
    
    for voice_id, text in voice_scripts.items():
        file_path = os.path.join(presets_dir, f"{voice_id}.wav")
        if not os.path.exists(file_path):
            if use_gtts:
                try:
                    # gTTS outputs MP3, we need to convert to WAV (24kHz mono)
                    mp3_path = file_path.replace(".wav", ".mp3")
                    tts = gTTS(text=text, lang="vi", slow=False)
                    tts.save(mp3_path)
                    
                    # Convert MP3 to WAV using ffmpeg
                    cmd = [
                        "ffmpeg", "-y", "-i", mp3_path,
                        "-ar", "24000", "-ac", "1",
                        "-acodec", "pcm_s16le",
                        file_path
                    ]
                    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    if result.returncode == 0:
                        os.remove(mp3_path)  # Clean up MP3
                        print(f"  -> Created preset (gTTS): {voice_id}.wav")
                    else:
                        # If ffmpeg fails, try direct approach with pydub
                        print(f"  -> FFmpeg conversion failed for {voice_id}, using MP3 directly")
                        os.rename(mp3_path, file_path)
                except Exception as e:
                    print(f"  -> gTTS failed for {voice_id}: {e}. Creating sine wave fallback.")
                    _create_sine_preset(file_path)
            else:
                _create_sine_preset(file_path)
        else:
            print(f"  -> Preset already exists: {voice_id}.wav")

def _create_sine_preset(file_path):
    """Fallback: create a sine wave preset if TTS is unavailable."""
    sample_rate = 24000
    duration = 5.0
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    data = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(file_path, data, sample_rate)
    print(f"  -> Created sine wave fallback: {os.path.basename(file_path)}")

def create_meme_videos(memes_dir):
    """
    Attempts to download real meme video templates from YouTube using yt-dlp,
    falling back to FFmpeg solid color backgrounds if the download fails.
    """
    print("[Setup] Generating video meme templates...")
    memes_sources = {
        "cat_talking": ('ytsearch1:"cat talking meme green screen"', "color=c=purple:s=640x360:d=5"),
        "minions": ('ytsearch1:"minions green screen"', "color=c=yellow:s=640x360:d=5"),
        "breaking_news": ('ytsearch1:"breaking news green screen template"', "color=c=red:s=640x360:d=5")
    }
    
    for meme_id, (search_query, fallback_filter) in memes_sources.items():
        file_path = os.path.join(memes_dir, f"{meme_id}.mp4")
        if not os.path.exists(file_path):
            success = False
            try:
                print(f"  -> Attempting to download real meme video for {meme_id}...")
                import json
                cmd_info = ["python", "-m", "yt_dlp", "--dump-json", "--no-warnings", search_query]
                res_info = subprocess.run(cmd_info, capture_output=True, text=True, check=True)
                info = json.loads(res_info.stdout.strip().split("\n")[0])
                video_url = info['webpage_url']
                
                temp_dl = f"temp_{meme_id}.mp4"
                cmd_dl = [
                    "python", "-m", "yt_dlp", 
                    "-f", "bestvideo[height<=480]+bestaudio/best[height<=480]/best", 
                    "-o", temp_dl, 
                    video_url
                ]
                subprocess.run(cmd_dl, check=True)
                
                # Cut to 5 seconds and scale/re-encode
                cmd_ffmpeg = [
                    "ffmpeg", "-y", "-i", temp_dl,
                    "-t", "5", "-c:v", "libx264", "-c:a", "aac",
                    "-pix_fmt", "yuv420p", "-vf", "scale=640:360",
                    file_path
                ]
                res_ffmpeg = subprocess.run(cmd_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                if os.path.exists(temp_dl):
                    try:
                        os.remove(temp_dl)
                    except Exception:
                        pass
                    
                if res_ffmpeg.returncode == 0:
                    print(f"  -> Successfully created real meme video: {file_path}")
                    success = True
                else:
                    print(f"  -> FFmpeg failed to process downloaded video for {meme_id}. Falling back to solid color.")
            except Exception as e:
                print(f"  -> Failed to download real video for {meme_id}: {e}. Falling back to solid color.")
            
            if not success:
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "lavfi", "-i", fallback_filter,
                    "-f", "lavfi", "-i", "sine=f=440:d=5",
                    "-c:v", "libx264", "-c:a", "aac",
                    "-pix_fmt", "yuv420p",
                    file_path
                ]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode != 0:
                    print(f"  [Error] FFmpeg solid color failed for {meme_id}: {result.stderr.decode('utf-8', errors='ignore')}")
                else:
                    print(f"  -> Created fallback solid color video: {file_path}")
        else:
            print(f"  -> Meme video already exists: {file_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    presets_dir = os.path.join(base_dir, "static", "presets")
    memes_dir = os.path.join(base_dir, "static", "memes")
    
    os.makedirs(presets_dir, exist_ok=True)
    os.makedirs(memes_dir, exist_ok=True)
    
    create_voice_presets(presets_dir)
    create_meme_videos(memes_dir)
    print("[Setup] Assets initialization complete!")
