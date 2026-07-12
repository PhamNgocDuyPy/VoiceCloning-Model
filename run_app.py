import os
import sys
import uvicorn

if __name__ == "__main__":
    # Add web_app to python path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    print("=" * 60)
    print("      Kich Hoat VoiceLab Web App - ElevenLabs Style")
    print("=" * 60)
    print("Giao dien chay tai: http://localhost:8000")
    print("Vui long mo trinh duyet va truy cap lien ket tren.")
    print("Nhan Ctrl+C de dung may chu.")
    print("=" * 60)
    
    uvicorn.run("web_app.backend.main:app", host="0.0.0.0", port=8000, reload=True)
