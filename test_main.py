import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import sys

# Mock heavy modules before importing main to prevent loading PyTorch or models
sys.modules['viterbox'] = MagicMock()
sys.modules['vieneu'] = MagicMock()
sys.modules['vieneu.base'] = MagicMock()
sys.modules['piper'] = MagicMock()
sys.modules['onnxruntime'] = MagicMock()
import transformers
import torch

from web_app.backend.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_dependencies():
    # Setup mocks
    with patch('web_app.backend.main.manager.get_engine') as mock_get_engine, \
         patch('web_app.backend.main.dub_video') as mock_dub_video, \
         patch('web_app.backend.main.concatenate_audios') as mock_concat, \
         patch('web_app.backend.utils.load_pronunciation_dict', return_value={}), \
         patch('web_app.backend.utils.save_pronunciation_dict', return_value=None), \
         patch('web_app.backend.utils.estimate_mos_score', return_value=4.5), \
         patch('soundfile.read', return_value=([0]*24000, 24000)), \
         patch('os.path.exists', return_value=True): # Mock exists globally for tests
         
        mock_engine = MagicMock()
        mock_engine.generate.return_value = None
        mock_get_engine.return_value = mock_engine
        mock_dub_video.return_value = "mocked_dubbed_video.mp4"
        mock_concat.return_value = "mocked_concatenated.wav"
        
        yield {
            "get_engine": mock_get_engine,
            "dub_video": mock_dub_video,
            "concatenate_audios": mock_concat
        }

def test_generate_preset():
    response = client.post("/api/generate", data={
        "text": "Hello world",
        "model": "viterbox",
        "voice": "do_mixi"
    })
    assert response.status_code == 200
    assert "audio_url" in response.json()

def test_generate_upload():
    # Test zero-shot with uploaded file
    file_content = b"fake audio content"
    response = client.post("/api/generate", data={
        "text": "Hello world",
        "model": "viterbox",
        "voice": "custom"
    }, files={
        "ref_audio": ("test.wav", file_content, "audio/wav")
    })
    assert response.status_code == 200
    assert "audio_url" in response.json()

def test_dub_meme():
    response = client.post("/api/dub-meme", json={
        "text": "Funny meme",
        "model": "viterbox",
        "voice": "do_mixi",
        "video_id": "meme1.mp4"
    })
    assert response.status_code == 200
    assert "video_url" in response.json()

def test_benchmark():
    response = client.post("/api/benchmark", json={
        "text": "Benchmark text"
    })
    assert response.status_code == 200
    res_json = response.json()
    assert "results" in res_json
    assert len(res_json["results"]) == 3
    assert any("Viterbox" in r["model"] for r in res_json["results"])

def test_chat():
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"choices": [{"message": {"content": "Mocked AI response"}}]}
    
    with patch('requests.post', return_value=mock_res):
        response = client.post("/api/chat", json={
            "message": "Hi AI",
            "character": "Einstein",
            "model": "viterbox",
            "voice": "do_mixi",
            "history": []
        })
        assert response.status_code == 200
        res = response.json()
        assert "text" in res
        assert "audio_url" in res
        assert res["text"] == "Mocked AI response"

def test_chat_pair():
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"choices": [{"message": {"content": '[{"character": "Einstein", "text": "Response 1"}, {"character": "Newton", "text": "Response 2"}]'}}]}
    
    with patch('requests.post', return_value=mock_res):
        response = client.post("/api/chat_pair", json={
            "topic": "Space",
            "char_a": "Einstein",
            "model_a": "viterbox",
            "voice_a": "do_mixi",
            "char_b": "Newton",
            "model_b": "piper",
            "voice_b": "vi_VN-25hours",
            "turns": 1
        })
        assert response.status_code == 200
        res = response.json()
        assert "dialogue" in res
        assert len(res["dialogue"]) == 2 # 1 turn each

def test_ab_test():
    # AB Test uses Form data not json!
    response = client.post("/api/ab-test", data={
        "text": "Compare these models",
        "model_a": "viterbox",
        "voice_a": "do_mixi",
        "model_b": "piper",
        "voice_b": "vi_VN-25hours"
    })
    assert response.status_code == 200
    res = response.json()
    assert "sample_a_url" in res
    assert "sample_b_url" in res

def test_get_pronunciation():
    response = client.get("/api/pronunciation")
    assert response.status_code == 200
    assert "items" in response.json()
    assert isinstance(response.json()["items"], list)

def test_post_pronunciation():
    response = client.post("/api/pronunciation", json={
        "original": "test",
        "replacement": "tét"
    })
    assert response.status_code == 200
    assert response.json()["message"] == "Success"
