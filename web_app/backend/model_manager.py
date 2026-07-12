import gc
import os
import threading
import torch

class ModelManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.active_model = None
        self.engines = {
            "vieneu": None,
            "vieneu_base": None,
            "viterbox": None,
            "piper": None
        }
        # Paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.presets_dir = os.path.join(self.base_dir, "static", "presets")
        self.outputs_dir = os.path.join(self.base_dir, "static", "outputs")
        self.memes_dir = os.path.join(self.base_dir, "static", "memes")
        
        # Ensure directories exist
        os.makedirs(self.presets_dir, exist_ok=True)
        os.makedirs(self.outputs_dir, exist_ok=True)
        os.makedirs(self.memes_dir, exist_ok=True)

    def get_engine(self, model_name: str):
        """
        Lazy load and return the requested TTS engine.
        If loading a heavy model, it unloads other heavy models to save RAM.
        """
        model_name = model_name.lower()
        if model_name not in self.engines:
            raise ValueError(f"Unknown model name: {model_name}")

        with self.lock:
            # If already loaded, return it
            if self.engines[model_name] is not None:
                return self.engines[model_name]

            print(f"[ModelManager] Loading model: {model_name}...")

            # Memory clean up if switching heavy models
            if model_name in ["vieneu", "vieneu_base", "viterbox"]:
                self._unload_heavy_models(exclude=model_name)

            # Load the requested model
            if model_name == "piper":
                from .tts_engines import PiperEngine
                self.engines["piper"] = PiperEngine(self)
            elif model_name == "vieneu":
                from .tts_engines import VieNeuEngine
                self.engines["vieneu"] = VieNeuEngine(self, is_base=False)
            elif model_name == "vieneu_base":
                from .tts_engines import VieNeuEngine
                self.engines["vieneu_base"] = VieNeuEngine(self, is_base=True)
            elif model_name == "viterbox":
                from .tts_engines import ViterboxEngine
                self.engines["viterbox"] = ViterboxEngine(self)

            self.active_model = model_name
            print(f"[ModelManager] Model {model_name} loaded successfully.")
            return self.engines[model_name]

    def _unload_heavy_models(self, exclude: str):
        """
        Unload heavy models (VieNeu and Viterbox) from RAM to avoid OOM.
        """
        unloaded = False
        for name in ["vieneu", "vieneu_base", "viterbox"]:
            if name != exclude and self.engines[name] is not None:
                print(f"[ModelManager] Unloading heavy model: {name} to free RAM...")
                self.engines[name] = None
                unloaded = True

        if unloaded:
            # Trigger Python garbage collection
            gc.collect()
            # If PyTorch was using any memory (even on CPU), empty cache / release memory back to OS
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print("[ModelManager] Memory clean up completed.")

# Single global manager instance
manager = ModelManager()
