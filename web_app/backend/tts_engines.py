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
        # Load VieNeu standard PyTorch v2 model
        from vieneu import Vieneu
        print("[VieNeu] Initializing standard PyTorch VieNeu-TTS engine...")
        self.tts = Vieneu(mode="standard", backbone_repo="pnnbao-ump/VieNeu-TTS-0.3B", backbone_device="cpu")
        
        if not is_base:
            # Load your custom fine-tuned LoRA adapter
            lora_path = os.path.join(self.manager.base_dir, "model")
            if os.path.exists(lora_path) and os.path.exists(os.path.join(lora_path, "adapter_config.json")):
                print(f"[VieNeu] Loading local LoRA adapter from: {lora_path}")
                self.tts.load_lora_adapter(lora_path)
            else:
                print("[VieNeu] [Warning] Local LoRA adapter folder 'model' not found. Using VieNeu base model.")

    def generate(self, text: str, voice_id: str = "SonTungMTP", ref_audio_path: str = None, output_path: str = "output.wav"):
        text = apply_pronunciation_dict(text)
        # Synthesize audio. It automatically resolves the voice (e.g. SonTungMTP) 
        # from the loaded voices.json in the LoRA folder.
        if voice_id == "custom":
            voice_id = None
        wav = self.tts.infer(text=text, voice=voice_id, ref_audio=ref_audio_path)
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
