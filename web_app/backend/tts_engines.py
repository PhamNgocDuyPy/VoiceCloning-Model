import os
import urllib.request
import numpy as np
import torch
import soundfile as sf
from .utils import apply_pronunciation_dict

class PiperEngine:
    def __init__(self, manager):
        self.manager = manager
        self.voices = {}
        
        # We support two voices for Piper
        self.voice_configs = {
            "vi_VN-25hours_single-low": {
                "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/25hours_single/low/vi_VN-25hours_single-low.onnx",
                "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/25hours_single/low/vi_VN-25hours_single-low.onnx.json"
            },
            "vi_VN-vivos-x_low": {
                "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/vivos/x_low/vi_VN-vivos-x_low.onnx",
                "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/vivos/x_low/vi_VN-vivos-x_low.onnx.json"
            },
            "vi_VN-vais1000-medium": {
                "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/vais1000/medium/vi_VN-vais1000-medium.onnx",
                "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/vais1000/medium/vi_VN-vais1000-medium.onnx.json"
            }
        }
        
        # Create a directory to store models
        self.models_dir = os.path.join(self.manager.base_dir, "models")
        os.makedirs(self.models_dir, exist_ok=True)

    def _get_voice(self, voice_id: str):
        if voice_id not in self.voice_configs:
            # Fallback to default
            voice_id = "vi_VN-25hours_single-low"
            
        if voice_id in self.voices:
            return self.voices[voice_id]
            
        # Download files if they don't exist
        onnx_path = os.path.join(self.models_dir, f"{voice_id}.onnx")
        json_path = f"{onnx_path}.json"
        
        config = self.voice_configs[voice_id]
        
        if not os.path.exists(onnx_path):
            print(f"[Piper] Downloading model {voice_id} from Hugging Face...")
            urllib.request.urlretrieve(config["onnx"], onnx_path)
        if not os.path.exists(json_path):
            print(f"[Piper] Downloading config {voice_id} from Hugging Face...")
            urllib.request.urlretrieve(config["json"], json_path)
            
        # Load the voice
        from piper import PiperVoice
        self.voices[voice_id] = PiperVoice.load(onnx_path, config_path=json_path)
        return self.voices[voice_id]

    def generate(self, text: str, voice_id: str, ref_audio_path: str = None, output_path: str = "output.wav"):
        import wave
        text = apply_pronunciation_dict(text)
        voice = self._get_voice(voice_id)
        with wave.open(output_path, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)
        print(f"[Piper] Audio generated successfully at: {output_path}")
        return output_path


class VieNeuEngine:
    def __init__(self, manager, is_base=False):
        self.manager = manager
        self.is_base = is_base
        
        # Load VieNeu standard PyTorch v2 model
        from vieneu import Vieneu
        print("[VieNeu] Initializing standard PyTorch VieNeu-TTS engine...")
        hf_token = os.getenv("HF_TOKEN")
        gguf = "VieNeu-TTS-v2-Q4-K-M.gguf" if is_base else None
        self.tts = Vieneu(
            mode="standard",
            backbone_repo="pnnbao-ump/VieNeu-TTS-v2",
            backbone_device="cpu",
            gguf_filename=gguf,
            codec_repo="neuphonic/neucodec",
            hf_token=hf_token
        )
        
        if not is_base:
            # Load your custom fine-tuned LoRA adapter
            lora_path = os.path.join(os.path.dirname(self.manager.base_dir), "model")
            if os.path.exists(lora_path) and os.path.exists(os.path.join(lora_path, "adapter_config.json")):
                print(f"[VieNeu] Loading local LoRA adapter from: {lora_path}")
                try:
                    self.tts.load_lora_adapter(lora_path, hf_token=hf_token)
                except Exception as e:
                    e_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
                    print(f"[VieNeu] [Warning] Failed to load LoRA on v2 base model: {e_msg}")
                    print("[VieNeu] This is likely because your LoRA adapter weights in 'model/' were trained on v1 (0.3B) rather than v2.")
                    print("[VieNeu] Falling back to VieNeu-TTS-0.3B (v1) base model...")
                    
                    # Re-initialize self.tts using the v1 base model (VieNeu-TTS-0.3B)
                    self.tts = Vieneu(
                        mode="standard",
                        backbone_repo="pnnbao-ump/VieNeu-TTS-0.3B",
                        backbone_device="cpu",
                        gguf_filename=None,
                        codec_repo="neuphonic/neucodec",
                        hf_token=hf_token
                    )
                    
                    # Re-try loading the LoRA adapter on the v1 base model
                    print(f"[VieNeu] Loading local LoRA adapter on v1 base model: {lora_path}")
                    self.tts.load_lora_adapter(lora_path, hf_token=hf_token)
                
                # Apply monkey patch to inject notebook-specific generation parameters for the fine-tuned LoRA model
                if hasattr(self.tts, "backbone") and self.tts.backbone is not None:
                    print("[VieNeu] Applying notebook-optimized generation hyper-parameters (repetition_penalty=1.2, top_p=0.9, temp=0.7)")
                    original_generate = self.tts.backbone.generate
                    def custom_generate(*args, **kwargs):
                        kwargs["repetition_penalty"] = 1.2
                        kwargs["top_p"] = 0.9
                        kwargs["temperature"] = 0.7
                        if "top_k" in kwargs:
                            del kwargs["top_k"]
                        return original_generate(*args, **kwargs)
                    self.tts.backbone.generate = custom_generate
            else:
                print("[VieNeu] [Warning] Local LoRA adapter folder 'model' not found. Using VieNeu base model.")
 
    def generate(self, text: str, voice_id: str = "SonTungMTP", ref_audio_path: str = None, output_path: str = "output.wav"):
        text = apply_pronunciation_dict(text)
        
        voice_data = None
        ref_codes = None
        ref_text = None

        if ref_audio_path:
            # Zero-shot cloning: encode the uploaded reference audio into codes directly
            try:
                ref_codes = self.tts.encode_reference(ref_audio_path)
                try:
                    default_voice = self.tts.get_preset_voice(None)
                    ref_text = default_voice.get("text", "Lúc nào cũng cười, Tùng lúc nào cũng tích cực. Vừa lúc nãy vừa cười to xong")
                except Exception:
                    ref_text = "Lúc nào cũng cười, Tùng lúc nào cũng tích cực. Vừa lúc nãy vừa cười to xong"
                print(f"[VieNeu] Using zero-shot cloning with custom ref audio")
            except Exception as e:
                e_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
                print(f"[VieNeu] [Warning] encode_reference failed: {e_msg}")
        else:
            # Use preset voice codes (from voices.json which is bundled with LoRA adapter or model)
            try:
                voice_data = self.tts.get_preset_voice(voice_id)
                print(f"[VieNeu] Using preset voice: {voice_id}")
            except Exception:
                try:
                    voice_data = self.tts.get_preset_voice(None)
                    print(f"[VieNeu] Using default preset voice")
                except Exception as e:
                    e_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
                    print(f"[VieNeu] [Warning] No preset voice found: {e_msg}. Falling back to hardcoded ref_text.")
                    # Use hardcoded ref_codes from voices.json on disk as last resort
                    try:
                        import json
                        voices_json_path = os.path.join(os.path.dirname(self.manager.base_dir), "model", "voices.json")
                        if os.path.exists(voices_json_path):
                            with open(voices_json_path, "r", encoding="utf-8") as f:
                                vdata = json.load(f)
                            first_preset = list(vdata.get("presets", {}).values())[0]
                            import numpy as np
                            ref_codes = np.array(first_preset["codes"], dtype=np.int64)
                            ref_text = first_preset.get("text", "Lúc nào cũng cười, Tùng lúc nào cũng tích cực.")
                            print(f"[VieNeu] Loaded ref_codes from voices.json directly")
                    except Exception as e2:
                        e_msg2 = str(e2).encode('ascii', errors='ignore').decode('ascii')
                        print(f"[VieNeu] [Warning] voices.json fallback failed: {e_msg2}")

        wav = self.tts.infer(
            text=text,
            voice=voice_data,
            ref_audio=None,
            ref_codes=ref_codes,
            ref_text=ref_text,
            apply_watermark=False
        )
        self.tts.save(wav, output_path)
        print(f"[VieNeu] Audio generated successfully at: {output_path}")
        return output_path


class ViterboxEngine:
    def __init__(self, manager):
        self.manager = manager
        from viterbox import Viterbox
        print("[Viterbox] Loading SOTA Viterbox model on CPU...")
        # Viterbox downloads its weights automatically on first load.
        # It takes ~1.5GB of RAM.
        import torch
        import transformers

        # Force eager attention for transformers to avoid SDPA returning None for attentions
        if hasattr(transformers.utils.import_utils, 'is_torch_sdpa_available'):
            transformers.utils.import_utils.is_torch_sdpa_available = lambda: False
            
        original_torch_load = torch.load

        def safe_torch_load(*args, **kwargs):
            if 'map_location' not in kwargs:
                kwargs['map_location'] = 'cpu'
            return original_torch_load(*args, **kwargs)

        torch.load = safe_torch_load
        try:
            self.tts = Viterbox.from_pretrained("cpu")
        finally:
            torch.load = original_torch_load

    def generate(self, text: str, voice_id: str = "amee", ref_audio_path: str = None, output_path: str = "output.wav"):
        text = apply_pronunciation_dict(text)
        prompt_path = None
        
        if voice_id == "custom":
            # If zero-shot cloning with custom upload
            if not ref_audio_path or not os.path.exists(ref_audio_path):
                raise ValueError("Reference audio path is required for custom Viterbox cloning.")
            prompt_path = ref_audio_path
        else:
            # Use preloaded famoso preset voice
            prompt_path = os.path.join(self.manager.presets_dir, f"{voice_id}.wav")
            if not os.path.exists(prompt_path):
                # Fallback to a placeholder or create a simple tone / download preset
                print(f"[Viterbox] Preset file not found: {prompt_path}. Attempting fallback...")
                # We can download a default preset or alert the user.
                # In main.py or run_app.py we can pre-configure reference voices.
                raise FileNotFoundError(f"Famous voice preset file not found: {prompt_path}. Please place reference audio in the static/presets folder.")

        print(f"[Viterbox] Generating speech using prompt: {prompt_path}")
        audio = self.tts.generate(
            text=text,
            language="vi",
            audio_prompt=prompt_path,
            exaggeration=0.5,
            cfg_weight=0.5,
            temperature=0.8,
            sentence_pause_ms=500
        )
        self.tts.save_audio(audio, output_path)
        print(f"[Viterbox] Audio generated successfully at: {output_path}")
        return output_path
