import subprocess
import os
import json
import numpy as np
from pydub import AudioSegment

# ========================================
# Pronunciation Dictionary
# ========================================
PRONUNCIATION_DICT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "pronunciation_dict.json"
)

def load_pronunciation_dict():
    """Load custom pronunciation dictionary from JSON file."""
    if os.path.exists(PRONUNCIATION_DICT_PATH):
        with open(PRONUNCIATION_DICT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_pronunciation_dict(entries: dict):
    """Save custom pronunciation dictionary to JSON file."""
    os.makedirs(os.path.dirname(PRONUNCIATION_DICT_PATH), exist_ok=True)
    with open(PRONUNCIATION_DICT_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

def apply_pronunciation_dict(text: str) -> str:
    """Apply pronunciation replacements to text before TTS inference.
    Replaces exact word matches using the saved dictionary."""
    pdict = load_pronunciation_dict()
    for original, replacement in pdict.items():
        text = text.replace(original, replacement)
    return text


# ========================================
# Pseudo-MOS Estimation (Lightweight)
# ========================================
def estimate_mos_score(audio_path: str) -> dict:
    """Estimate a pseudo-MOS (Mean Opinion Score) from audio file.
    
    Uses signal-level heuristics (no heavy ML model required):
    - SNR estimation → naturalness proxy
    - Spectral flatness → clarity proxy  
    - Zero-crossing rate → articulation proxy
    - RMS energy consistency → stability proxy
    
    Returns a dict with individual scores and overall MOS (1.0–5.0).
    """
    try:
        import soundfile as sf
        data, sr = sf.read(audio_path)
        
        if len(data) == 0:
            return {"overall": 1.0, "naturalness": 1.0, "clarity": 1.0, "stability": 1.0}
        
        # Ensure mono
        if data.ndim > 1:
            data = data.mean(axis=1)
        
        # 1. RMS Energy → volume consistency
        frame_size = int(0.025 * sr)  # 25ms frames
        hop = int(0.010 * sr)         # 10ms hop
        frames = [data[i:i+frame_size] for i in range(0, len(data) - frame_size, hop)]
        
        if len(frames) < 2:
            return {"overall": 2.0, "naturalness": 2.0, "clarity": 2.0, "stability": 2.0}
        
        rms_values = [np.sqrt(np.mean(f**2)) for f in frames]
        rms_arr = np.array(rms_values)
        
        # Filter out silence frames
        voiced_rms = rms_arr[rms_arr > 0.01]
        
        if len(voiced_rms) < 2:
            return {"overall": 2.0, "naturalness": 2.0, "clarity": 2.0, "stability": 2.0}
        
        # Stability: lower coefficient of variation = more stable energy
        cv = np.std(voiced_rms) / (np.mean(voiced_rms) + 1e-8)
        stability_score = np.clip(5.0 - cv * 4.0, 1.0, 5.0)
        
        # 2. SNR estimation (signal vs noise floor)
        signal_power = np.mean(voiced_rms**2)
        noise_floor = np.percentile(rms_arr, 5)**2 + 1e-12
        snr_db = 10 * np.log10(signal_power / noise_floor)
        # Map SNR: 0dB→1.0, 10dB→2.5, 20dB→4.0, 30+dB→5.0
        naturalness_score = np.clip(1.0 + snr_db * 0.133, 1.0, 5.0)
        
        # 3. Spectral flatness → clarity
        # Use FFT on voiced segments
        voiced_data = data[np.abs(data) > 0.01]
        if len(voiced_data) > 1024:
            fft = np.abs(np.fft.rfft(voiced_data[:4096]))
            fft = fft[1:]  # remove DC
            fft = fft + 1e-12  # avoid log(0)
            geo_mean = np.exp(np.mean(np.log(fft)))
            arith_mean = np.mean(fft)
            spectral_flatness = geo_mean / (arith_mean + 1e-12)
            # Lower flatness = more tonal/clear speech (good)
            # Flatness near 1.0 = noise-like (bad)
            clarity_score = np.clip(5.0 - spectral_flatness * 6.0, 1.0, 5.0)
        else:
            clarity_score = 2.5
        
        # Overall MOS = weighted average
        overall = 0.35 * naturalness_score + 0.35 * clarity_score + 0.30 * stability_score
        overall = round(np.clip(overall, 1.0, 5.0), 2)
        
        return {
            "overall": overall,
            "naturalness": round(float(naturalness_score), 2),
            "clarity": round(float(clarity_score), 2),
            "stability": round(float(stability_score), 2)
        }
        
    except Exception as e:
        print(f"[MOS] Error estimating MOS: {e}")
        return {"overall": 2.5, "naturalness": 2.5, "clarity": 2.5, "stability": 2.5}


# ========================================
# Video Dubbing (FFmpeg)
# ========================================
def dub_video(video_path: str, audio_path: str, output_path: str) -> str:
    """
    Dubs the generated audio onto a video clip using FFmpeg.
    Uses copy-codec for video to ensure it runs instantly on CPU without re-encoding.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # FFmpeg command:
    # -y: overwrite output file
    # -i: inputs
    # -c:v copy: copy video stream without re-encoding (instant!)
    # -c:a aac: encode audio to AAC
    # -map 0:v:0 -map 1:a:0: map first video stream and first audio stream
    # -shortest: end output when the shortest input (video or audio) ends
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]

    print(f"[Utils] Running FFmpeg command: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
    
    print(f"[Utils] Video dubbed successfully: {output_path}")
    return output_path

def concatenate_audios(audio_paths: list, output_path: str, pause_ms: int = 500) -> str:
    """
    Stitches multiple audio segments together into a single WAV file,
    adding a silent pause (in ms) between each segment.
    """
    if not audio_paths:
        raise ValueError("Audio paths list is empty")

    combined = AudioSegment.empty()
    silence = AudioSegment.silent(duration=pause_ms)

    for i, path in enumerate(audio_paths):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Audio file not found: {path}")
        
        segment = AudioSegment.from_wav(path)
        combined += segment
        
        # Add silence between segments (but not after the last one)
        if i < len(audio_paths) - 1:
            combined += silence

    combined.export(output_path, format="wav")
    print(f"[Utils] Concatenated {len(audio_paths)} audios into: {output_path}")
    return output_path
