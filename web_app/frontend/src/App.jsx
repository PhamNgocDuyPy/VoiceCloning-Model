import React, { useState, useEffect, useRef } from "react";
import WaveSurfer from "wavesurfer.js";
import {
  Play,
  Pause,
  Microphone,
  Upload,
  Plus,
  Trash,
  Sliders,
  ChartBar,
  ChatCircleText,
  User,
  X,
  FileAudio,
  Check,
  Video,
  Key
} from "@phosphor-icons/react";
import bgImage from "./assets/bg.png";

// --- Custom Waveform Player using WaveSurfer.js ---
function WaveformPlayer({ url }) {
  const containerRef = useRef(null);
  const wavesurferRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (!containerRef.current || !url) return;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: "#e7e5e4",      // hairline light gray
      progressColor: "#0c0a09",  // deep ink black
      cursorColor: "#0c0a09",
      barWidth: 2,
      barGap: 3,
      barRadius: 2,
      height: 60,
      normalize: true,
      responsive: true
    });

    ws.load(url);
    wavesurferRef.current = ws;

    ws.on("play", () => setIsPlaying(true));
    ws.on("pause", () => setIsPlaying(false));
    ws.on("finish", () => setIsPlaying(false));

    return () => {
      ws.destroy();
    };
  }, [url]);

  const handlePlayPause = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.playPause();
    }
  };

  return (
    <div className="flex items-center gap-4 bg-white p-4 border border-hairline rounded-xl w-full shadow-sm">
      <button
        onClick={handlePlayPause}
        className="w-12 h-12 flex items-center justify-center bg-ink text-white rounded-full hover:bg-primary transition-all duration-200 cursor-pointer shadow-sm active:scale-95"
      >
        {isPlaying ? <Pause size={24} weight="fill" /> : <Play size={24} weight="fill" />}
      </button>
      <div ref={containerRef} className="flex-1 min-w-0" />
    </div>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState("tts");

  // System voices list mapped by model
  const voicesByModel = {
    piper: [
      { id: "vi_VN-25hours_single-low", name: "Giọng đọc vi_VN 25h (Nam miền Nam)", type: "Standard" },
      { id: "vi_VN-vivos-x_low", name: "Giọng đọc VIVOS (Nữ miền Nam)", type: "Standard" },
      { id: "vi_VN-vais1000-medium", name: "Giọng đọc VAIS 1000 (Trung bình - Mới)", type: "Standard" }
    ],
    vieneu: [
      { id: "SonTungMTP", name: "Sơn Tùng MTP (LoRA)", type: "Custom" }
    ],
    vieneu_base: [
      { id: "custom", name: "[Zero-Shot] Tải lên giọng của bạn", type: "Custom" },
      { id: "Bình", name: "Bình (Giọng nam)", type: "Standard" },
      { id: "Tuyên", name: "Phạm Tuyên (Giọng nam)", type: "Standard" },
      { id: "Vinh", name: "Vinh (Giọng nam)", type: "Standard" },
      { id: "Đoàn", name: "Đoàn (Giọng nam)", type: "Standard" },
      { id: "Lý", name: "Lý (Giọng nữ)", type: "Standard" },
      { id: "Ngọc", name: "Ngọc (Giọng nữ)", type: "Standard" },
      { id: "Trúc Ly", name: "Trúc Ly (Giọng nữ)", type: "Standard" }
    ],
    viterbox: [
      { id: "amee", name: "Amee (Preset)", type: "Celebrity" },
      { id: "do_mixi", name: "Độ Mixi (Preset)", type: "Celebrity" },
      { id: "barack_obama", name: "Barack Obama (Preset)", type: "Celebrity" },
      { id: "donald_trump", name: "Donald Trump (Preset)", type: "Celebrity" },
      { id: "tran_thanh", name: "MC Trấn Thành (Preset)", type: "Celebrity" },
      { id: "custom", name: "[Zero-Shot] Tải lên / Ghi âm giọng của bạn", type: "Custom" }
    ]
  };

  // --- State for Single Text to Speech ---
  const [ttsModel, setTtsModel] = useState("piper");
  const [ttsVoice, setTtsVoice] = useState("vi_VN-25hours_single-low");
  const [ttsText, setTtsText] = useState("Xin chào các bạn Sky ơi, hôm nay các bạn thế nào rồi?");
  const [refAudioFile, setRefAudioFile] = useState(null);
  const [refAudioName, setRefAudioName] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [ttsAudioUrl, setTtsAudioUrl] = useState("");
  const [ttsLoading, setTtsLoading] = useState(false);

  // Sync default voice on model select
  useEffect(() => {
    setTtsVoice(voicesByModel[ttsModel][0].id);
    setRefAudioFile(null);
    setRefAudioName("");
  }, [ttsModel]);

  // Handle file select for custom clone
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setRefAudioFile(file);
      setRefAudioName(file.name);
    }
  };

  // Micro recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: "audio/wav" });
        const file = new File([blob], "recorded_voice.wav", { type: "audio/wav" });
        setRefAudioFile(file);
        setRefAudioName("Microphone_Record.wav");
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (err) {
      alert("Không thể truy cập Microphone: " + err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const handleGenerateTts = async () => {
    if (!ttsText.trim()) return alert("Vui lòng nhập văn bản cần chuyển đổi.");
    if (ttsModel === "viterbox" && ttsVoice === "custom" && !refAudioFile) {
      return alert("Vui lòng tải lên hoặc ghi âm một tệp giọng nói mẫu để thực hiện Zero-Shot Cloning.");
    }

    setTtsLoading(true);
    setTtsAudioUrl("");

    const formData = new FormData();
    formData.append("text", ttsText);
    formData.append("model", ttsModel);
    formData.append("voice", ttsVoice);
    if (refAudioFile) {
      formData.append("ref_audio", refAudioFile);
    }

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setTtsAudioUrl(data.audio_url);
      } else {
        alert("Lỗi: " + (data.detail || "Không thể sinh giọng nói."));
      }
    } catch (err) {
      alert("Lỗi kết nối API: " + err);
    } finally {
      setTtsLoading(false);
    }
  };



  // --- State for Meme Video Dubbing ---
  const memesList = [
    { id: "cat_talking", name: "Talking Cat", description: "Chú mèo tranh luận ngộ nghĩnh", color: "bg-orb-rose/30" },
    { id: "minions", name: "Minions", description: "Lũ chuối vàng vui nhộn nói chuyện", color: "bg-orb-peach/30" },
    { id: "breaking_news", name: "Bản tin Thời sự", description: "Thông báo tin tức nóng sốt", color: "bg-orb-mint/30" }
  ];
  const [selectedMeme, setSelectedMeme] = useState("cat_talking");
  const [memeModel, setMemeModel] = useState("vieneu");
  const [memeVoice, setMemeVoice] = useState("SonTungMTP");
  const [memeText, setMemeText] = useState("Chào các bạn, hôm nay tôi sẽ đưa các bạn đi ăn phở Hà Nội ngon tuyệt vời!");
  const [dubbedVideoUrl, setDubbedVideoUrl] = useState("");
  const [dubbingLoading, setDubbingLoading] = useState(false);

  // Sync meme voices
  useEffect(() => {
    setMemeVoice(voicesByModel[memeModel][0].id);
  }, [memeModel]);

  const handleGenerateDubbing = async () => {
    if (!memeText.trim()) return alert("Vui lòng nhập câu thoại lồng tiếng.");
    setDubbingLoading(true);
    setDubbedVideoUrl("");

    try {
      const res = await fetch("/api/dub-meme", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: memeText,
          model: memeModel,
          voice: memeVoice,
          video_id: selectedMeme
        })
      });
      const data = await res.json();
      if (res.ok) {
        setDubbedVideoUrl(data.video_url);
      } else {
        alert("Lỗi: " + (data.detail || "Không thể lồng tiếng meme."));
      }
    } catch (err) {
      alert("Lỗi kết nối API: " + err);
    } finally {
      setDubbingLoading(false);
    }
  };

  // --- State for Model Benchmarks ---
  const [benchmarkText, setBenchmarkText] = useState("Học sinh Việt Nam chế tạo rô-bốt đạt huy chương vàng quốc tế tại cuộc thi khoa học.");
  const [benchmarkResults, setBenchmarkResults] = useState(null);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);

  const handleRunBenchmark = async () => {
    if (!benchmarkText.trim()) return alert("Vui lòng nhập câu thử nghiệm.");
    setBenchmarkLoading(true);
    setBenchmarkResults(null);

    try {
      const res = await fetch("/api/benchmark", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: benchmarkText })
      });
      const data = await res.json();
      if (res.ok) {
        setBenchmarkResults(data.results);
      } else {
        alert("Lỗi: " + (data.detail || "Không thể thực hiện benchmark."));
      }
    } catch (err) {
      alert("Lỗi kết nối API: " + err);
    } finally {
      setBenchmarkLoading(false);
    }
  };

  // --- State for A/B Blind Test ---
  const [abText, setAbText] = useState("Vui lòng nghe thử 2 giọng đọc dưới đây và bình chọn giọng nào tự nhiên hơn.");
  const [abModels, setAbModels] = useState({ modelA: "piper", voiceA: "vi_VN-25hours_single-low", modelB: "vieneu", voiceB: "SonTungMTP" });
  const [abRefAudioA, setAbRefAudioA] = useState(null);
  const [abRefAudioB, setAbRefAudioB] = useState(null);
  const [abResults, setAbResults] = useState(null);
  const [abLoading, setAbLoading] = useState(false);
  const [abVoteResult, setAbVoteResult] = useState(null);

  const handleRunAbTest = async () => {
    if (!abText.trim()) return alert("Vui lòng nhập văn bản.");
    setAbLoading(true);
    setAbResults(null);
    setAbVoteResult(null);

    try {
      const formData = new FormData();
      formData.append("text", abText);
      formData.append("model_a", abModels.modelA);
      formData.append("voice_a", abModels.voiceA);
      formData.append("model_b", abModels.modelB);
      formData.append("voice_b", abModels.voiceB);
      if (abRefAudioA) formData.append("ref_audio_a", abRefAudioA);
      if (abRefAudioB) formData.append("ref_audio_b", abRefAudioB);

      const res = await fetch("/api/ab-test", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        // Randomize order to be truly blind
        const isASample1 = Math.random() > 0.5;
        setAbResults({
          sample1: isASample1 ? data.sample_a_url : data.sample_b_url,
          sample2: isASample1 ? data.sample_b_url : data.sample_a_url,
          trueA: isASample1 ? 1 : 2,
          modelsInfo: { 1: abModels.modelA, 2: abModels.modelB }
        });
      } else alert("Lỗi: " + data.detail);
    } catch (err) { alert("Lỗi kết nối: " + err); } finally { setAbLoading(false); }
  };

  const handleAbVote = (choice) => {
    setAbVoteResult({
      choice,
      winnerInfo: abResults.trueA === choice ? "Mẫu A" : "Mẫu B",
      winnerModel: abResults.modelsInfo[choice]
    });
  };

  // --- State for Pronunciation Editor ---
  const [pronunciationDict, setPronunciationDict] = useState([]);
  const [newPronun, setNewPronun] = useState({ original: "", replacement: "" });

  useEffect(() => {
    if (activeTab === "pronunciation") {
      fetch("/api/pronunciation").then(r => r.json()).then(d => setPronunciationDict(d.items || [])).catch(e => console.error(e));
    }
  }, [activeTab]);

  const handleAddPronun = async () => {
    if (!newPronun.original || !newPronun.replacement) return;
    await fetch("/api/pronunciation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newPronun)
    });
    setNewPronun({ original: "", replacement: "" });
    fetch("/api/pronunciation").then(r => r.json()).then(d => setPronunciationDict(d.items || []));
  };

  const handleDeletePronun = async (word) => {
    await fetch(`/api/pronunciation/${word}`, { method: "DELETE" });
    fetch("/api/pronunciation").then(r => r.json()).then(d => setPronunciationDict(d.items || []));
  };

  // --- State for AI Chat Partner (Creative Feature) ---
  const characters = [
    { id: "SonTungMTP", name: "Sơn Tùng MTP", model: "vieneu", voice: "SonTungMTP", desc: "Ca sĩ vạn người mê, ấm áp và thân thiện", color: "bg-orb-rose" },
    { id: "do_mixi", name: "Tộc trưởng Độ Mixi", model: "viterbox", voice: "do_mixi", desc: "Anh trai quốc dân hài hước, bỗ bã và thẳng thắn", color: "bg-orb-sky" },
    { id: "tran_thanh", name: "Trấn Thành", model: "viterbox", voice: "tran_thanh", desc: "MC đa tài giàu cảm xúc, thích triết lý cuộc sống", color: "bg-orb-lavender" },
    { id: "barack_obama", name: "Barack Obama", model: "viterbox", voice: "barack_obama", desc: "Cựu tổng thống Mỹ, điềm tĩnh và truyền cảm hứng", color: "bg-orb-peach" },
    { id: "donald_trump", name: "Donald Trump", model: "viterbox", voice: "donald_trump", desc: "Tổng thống mạnh mẽ, tự tin và đầy năng lượng", color: "bg-orb-mint" }
  ];

  const [chatMode, setChatMode] = useState("single");
  
  // Single Chat States
  const [activeChar, setActiveChar] = useState(characters[0]);
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [chatAudioUrl, setChatAudioUrl] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatBottomRef = useRef(null);

  // Pair Chat States
  const [pairCharA, setPairCharA] = useState(characters[0]);
  const [pairCharB, setPairCharB] = useState(characters[1]);
  const [pairTopic, setPairTopic] = useState("Chuyện ăn sáng ở Việt Nam");
  const [pairDialogue, setPairDialogue] = useState([]);
  const [pairLoading, setPairLoading] = useState(false);
  // Audio playback state for pair
  const [currentPlayingIndex, setCurrentPlayingIndex] = useState(-1);

  // Sync single chat partner on character switch
  useEffect(() => {
    const greetingMap = {
      SonTungMTP: "Sky ơi! Anh Tùng ở đây rồi. Hôm nay em có gì vui kể anh nghe xem nào? 😉",
      do_mixi: "Hế nhô anh em nhé! Độ Mixi Phùng Thanh Độ đây, hôm nay có chuyện gì mà tìm tôi thế ông bạn?",
      tran_thanh: "Chào bạn. Thành rất vui được trò chuyện với bạn ngày hôm nay. Chúng ta cùng chia sẻ cuộc sống nhé.",
      barack_obama: "Hello. Barack Obama here. I'm pleased to chat with you. How can we make things better today?",
      donald_trump: "Hello! Donald Trump here. We are going to have the greatest chat, absolutely tremendous, believe me!"
    };
    setChatHistory([
      { role: "assistant", content: greetingMap[activeChar.id] }
    ]);
    setChatAudioUrl("");
  }, [activeChar]);

  // Scroll chat window to bottom
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, pairDialogue]);

  const handleSendChatMessage = async () => {
    if (!chatInput.trim()) return;
    const userMsg = chatInput;
    setChatInput("");
    setChatAudioUrl("");

    const updatedHistory = [...chatHistory, { role: "user", content: userMsg }];
    setChatHistory(updatedHistory);
    setChatLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg,
          character: activeChar.id,
          model: activeChar.model,
          voice: activeChar.voice,
          history: updatedHistory
        })
      });
      const data = await res.json();
      if (res.ok) {
        setChatHistory([...updatedHistory, { role: "assistant", content: data.text }]);
        setChatAudioUrl(data.audio_url);
        const audio = new Audio(data.audio_url);
        audio.play().catch((e) => console.log("Không thể tự động phát:", e));
      } else {
        alert("Lỗi: " + (data.detail || "Không có phản hồi từ máy chủ."));
      }
    } catch (err) {
      alert("Lỗi kết nối API: " + err);
    } finally {
      setChatLoading(false);
    }
  };

  const handleGeneratePairChat = async () => {
    if (!pairTopic.trim()) return alert("Vui lòng nhập chủ đề!");
    if (pairCharA.id === pairCharB.id) return alert("Vui lòng chọn 2 nhân vật khác nhau!");
    
    setPairLoading(true);
    setPairDialogue([]);
    setCurrentPlayingIndex(-1);

    try {
      const res = await fetch("/api/chat_pair", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: pairTopic,
          char_a: pairCharA.id,
          model_a: pairCharA.model,
          voice_a: pairCharA.voice,
          char_b: pairCharB.id,
          model_b: pairCharB.model,
          voice_b: pairCharB.voice,
          turns: 2
        })
      });
      const data = await res.json();
      if (res.ok) {
        setPairDialogue(data.dialogue);
        // Autoplay the first audio
        if (data.dialogue && data.dialogue.length > 0) {
           setCurrentPlayingIndex(0);
        }
      } else {
        alert("Lỗi sinh hội thoại: " + (data.detail || "Unknown Error"));
      }
    } catch (err) {
      alert("Lỗi kết nối API: " + err);
    } finally {
      setPairLoading(false);
    }
  };

  useEffect(() => {
    // Auto-play the sequence of pair dialogue
    if (currentPlayingIndex >= 0 && currentPlayingIndex < pairDialogue.length) {
       const audioUrl = pairDialogue[currentPlayingIndex].audio_url;
       if (audioUrl) {
         const audio = new Audio(audioUrl);
         audio.play().catch(e => console.log("Auto-play blocked"));
         audio.onended = () => {
           setCurrentPlayingIndex(prev => prev + 1);
         };
       } else {
         setCurrentPlayingIndex(prev => prev + 1);
       }
    }
  }, [currentPlayingIndex, pairDialogue]);

  return (
    <div className="relative z-0 flex h-[100dvh] overflow-hidden font-sans bg-white/40">
      
      {/* Rich Premium Background Image */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat pointer-events-none -z-20 opacity-100" 
        style={{ backgroundImage: `url(${bgImage})` }}
      />
      
      {/* Decorative Atmospheric Radial-Gradient Orbs (Framer-style drifting background) */}
      <div className="absolute top-12 left-1/4 w-[500px] h-[500px] rounded-full bg-orb-mint/40 filter blur-[100px] pointer-events-none -z-10 orb-float-1" />
      <div className="absolute top-1/3 right-1/4 w-[400px] h-[400px] rounded-full bg-orb-peach/40 filter blur-[100px] pointer-events-none -z-10 orb-float-2" />
      <div className="absolute bottom-1/4 left-1/3 w-[450px] h-[450px] rounded-full bg-orb-lavender/40 filter blur-[90px] pointer-events-none -z-10 orb-float-3" />

      {/* --- Sidebar Navigation (Desktop) --- */}
      <aside className="hidden lg:flex flex-col w-64 border-r border-hairline bg-white/60 backdrop-blur-xl shrink-0 z-40 shadow-[4px_0_24px_rgba(0,0,0,0.02)]">
        <div className="p-6">
          <span className="font-display text-2xl tracking-tighter text-ink font-light select-none">
            Voice<span className="font-sans font-medium text-lg tracking-normal ml-0.5">Lab</span>
          </span>
        </div>

        <nav className="flex-1 px-4 py-2 space-y-1.5 overflow-y-auto scrollbar-none">
          <button
            onClick={() => setActiveTab("tts")}
            className={`w-full text-left px-4 py-2.5 text-sm font-medium rounded-xl cursor-pointer transition-all ${
              activeTab === "tts" ? "bg-primary text-white shadow-sm ring-1 ring-primary/20" : "text-body hover:bg-surface-strong hover:text-ink"
            }`}
          >
            Speech Synthesis
          </button>

          <button
            onClick={() => setActiveTab("meme")}
            className={`w-full text-left px-4 py-2.5 text-sm font-medium rounded-xl cursor-pointer transition-all ${
              activeTab === "meme" ? "bg-primary text-white shadow-sm ring-1 ring-primary/20" : "text-body hover:bg-surface-strong hover:text-ink"
            }`}
          >
            Meme Dubbing
          </button>
          <button
            onClick={() => setActiveTab("benchmark")}
            className={`w-full text-left px-4 py-2.5 text-sm font-medium rounded-xl cursor-pointer transition-all ${
              activeTab === "benchmark" ? "bg-primary text-white shadow-sm ring-1 ring-primary/20" : "text-body hover:bg-surface-strong hover:text-ink"
            }`}
          >
            Model Benchmark
          </button>
          <button
            onClick={() => setActiveTab("ab_test")}
            className={`w-full text-left px-4 py-2.5 text-sm font-medium rounded-xl cursor-pointer transition-all ${
              activeTab === "ab_test" ? "bg-primary text-white shadow-sm ring-1 ring-primary/20" : "text-body hover:bg-surface-strong hover:text-ink"
            }`}
          >
            A/B Blind Test
          </button>
          <button
            onClick={() => setActiveTab("pronunciation")}
            className={`w-full text-left px-4 py-2.5 text-sm font-medium rounded-xl cursor-pointer transition-all ${
              activeTab === "pronunciation" ? "bg-primary text-white shadow-sm ring-1 ring-primary/20" : "text-body hover:bg-surface-strong hover:text-ink"
            }`}
          >
            Pronunciation Dictionary
          </button>
          <button
            onClick={() => setActiveTab("chat")}
            className={`w-full text-left px-4 py-2.5 text-sm font-medium rounded-xl cursor-pointer transition-all flex items-center justify-between ${
              activeTab === "chat" ? "bg-primary text-white shadow-sm ring-1 ring-primary/20" : "text-body hover:bg-surface-strong hover:text-ink"
            }`}
          >
            <span>AI Chat Partner</span>
            <ChatCircleText size={16} className={activeTab === "chat" ? "text-white/80" : "opacity-70"} />
          </button>
        </nav>
      </aside>

      {/* --- Main Area --- */}
      <main className="flex-1 h-full overflow-y-auto pb-16 relative z-10 scrollbar-thin">
        
        {/* Mobile Header (Only visible on lg:hidden) */}
        <div className="lg:hidden sticky top-0 bg-white/80 backdrop-blur-md border-b border-hairline px-6 py-4 flex items-center justify-between z-40 mb-6 shadow-sm">
          <span className="font-display text-xl tracking-tighter text-ink font-light select-none">
            Voice<span className="font-sans font-medium text-base tracking-normal ml-0.5">Lab</span>
          </span>
        </div>

        <div className="max-w-4xl mx-auto px-6 lg:mt-12">

          {/* Dynamic Mobile Nav Dropdown if screen size is small */}
          <div className="lg:hidden mb-6 flex overflow-x-auto gap-2 pb-2 scrollbar-none">
          <button
            onClick={() => setActiveTab("tts")}
            className={`whitespace-nowrap px-4 py-1.5 text-xs font-semibold rounded-full ${
              activeTab === "tts" ? "bg-primary text-white" : "bg-white text-body border border-hairline"
            }`}
          >
            Speech Synthesis
          </button>
          <button
            onClick={() => setActiveTab("meme")}
            className={`whitespace-nowrap px-4 py-1.5 text-xs font-semibold rounded-full ${
              activeTab === "meme" ? "bg-primary text-white" : "bg-white text-body border border-hairline"
            }`}
          >
            Meme Dubbing
          </button>
          <button
            onClick={() => setActiveTab("benchmark")}
            className={`whitespace-nowrap px-4 py-1.5 text-xs font-semibold rounded-full ${
              activeTab === "benchmark" ? "bg-primary text-white" : "bg-white text-body border border-hairline"
            }`}
          >
            Benchmarks
          </button>
          <button
            onClick={() => setActiveTab("chat")}
            className={`whitespace-nowrap px-4 py-1.5 text-xs font-semibold rounded-full flex items-center gap-1 ${
              activeTab === "chat" ? "bg-primary text-white" : "bg-white text-body border border-hairline"
            }`}
          >
            <ChatCircleText size={14} /> Chat Partner
          </button>
          <button
            onClick={() => setActiveTab("ab_test")}
            className={`whitespace-nowrap px-4 py-1.5 text-xs font-semibold rounded-full ${
              activeTab === "ab_test" ? "bg-primary text-white" : "bg-white text-body border border-hairline"
            }`}
          >
            A/B Test
          </button>
          <button
            onClick={() => setActiveTab("pronunciation")}
            className={`whitespace-nowrap px-4 py-1.5 text-xs font-semibold rounded-full ${
              activeTab === "pronunciation" ? "bg-primary text-white" : "bg-white text-body border border-hairline"
            }`}
          >
            Dictionary
          </button>
        </div>

        {/* --- Hero Section --- */}
        <section className="text-center mb-10 pt-4 relative">
          <div className="absolute inset-0 bg-white/40 blur-[80px] -z-10 rounded-[100%] max-w-2xl mx-auto h-full pointer-events-none" />
          <h1 className="font-display text-5xl md:text-6xl text-ink font-medium tracking-tighter leading-none mb-4 select-none drop-shadow-md">
            Nền tảng giả lập giọng nói Việt
          </h1>
          <p className="text-body text-base max-w-[60ch] mx-auto body-spaced font-medium text-opacity-100 drop-shadow-sm">
            Trải nghiệm nhân bản zero-shot, tạo hội thoại đa giọng nói, lồng tiếng video meme và trò chuyện với nghệ sĩ mô phỏng.
          </p>
        </section>

        {/* ======================================================== */}
        {/* --- TAB Content: Text To Speech --- */}
        {/* ======================================================== */}
        {activeTab === "tts" && (
          <div className="space-y-6">
            <div className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] space-y-6">
              
              {/* Textarea Input */}
              <div className="space-y-2">
                <label className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80">
                  Văn bản muốn đọc
                </label>
                <textarea
                  value={ttsText}
                  onChange={(e) => setTtsText(e.target.value)}
                  placeholder="Hãy nhập văn bản tại đây..."
                  rows={4}
                  className="w-full text-base p-4 border border-hairline-strong rounded-xl outline-none focus:border-ink transition-colors resize-none placeholder-stone-400"
                />
              </div>

              {/* Configure Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* TTS Model Select */}
                <div className="space-y-2">
                  <label className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80">
                    Mô hình giọng nói
                  </label>
                  <select
                    value={ttsModel}
                    onChange={(e) => setTtsModel(e.target.value)}
                    className="w-full h-11 px-3 border border-hairline-strong rounded-xl outline-none bg-white font-sans text-sm focus:border-ink transition-colors cursor-pointer"
                  >
                    <option value="piper">Piper (Lightweight)</option>
                    <option value="vieneu">VieNeu-TTS (LoRA Fine-tuned)</option>
                    <option value="vieneu_base">VieNeu-TTS (Base - Zero-shot)</option>
                    <option value="viterbox">Viterbox (Flow-matching)</option>
                  </select>
                </div>

                {/* Voice Selection */}
                <div className="space-y-2">
                  <label className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80">
                    Giọng nói
                  </label>
                  <select
                    value={ttsVoice}
                    onChange={(e) => setTtsVoice(e.target.value)}
                    className="w-full h-11 px-3 border border-hairline-strong rounded-xl outline-none bg-white font-sans text-sm focus:border-ink transition-colors cursor-pointer"
                  >
                    {voicesByModel[ttsModel]?.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Zero-Shot Custom Voice Upload/Record Panel */}
              {(ttsModel === "viterbox" || ttsModel.startsWith("vieneu")) && (
                <div className="border border-dashed border-hairline-strong rounded-xl p-6 bg-canvas-soft flex flex-col items-center gap-4 text-center">
                  <div className="flex items-center justify-center w-12 h-12 rounded-full bg-surface-strong border border-hairline">
                    <FileAudio size={24} className="text-body" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm text-ink mb-1">Mẫu giọng nói Zero-Shot</h3>
                    <p className="text-xs text-body text-opacity-70 max-w-[50ch]">
                      Vui lòng tải lên tệp âm thanh (WAV/MP3, khoảng 5-10 giây) hoặc ghi âm bằng microphone để huấn luyện tức thì mô hình nhân bản.
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 justify-center">
                    
                    {/* Native File Upload */}
                    <label className="h-10 px-4 flex items-center gap-2 border border-hairline-strong rounded-full bg-white text-sm font-medium hover:bg-surface-strong cursor-pointer transition-colors shadow-sm select-none active:scale-95">
                      <Upload size={16} />
                      Tải lên tệp
                      <input
                        type="file"
                        accept="audio/*"
                        onChange={handleFileChange}
                        className="hidden"
                      />
                    </label>

                    {/* Microphone Record */}
                    {isRecording ? (
                      <button
                        onClick={stopRecording}
                        className="h-10 px-4 flex items-center gap-2 border border-red-500 rounded-full bg-red-50 text-red-600 text-sm font-medium hover:bg-red-100 cursor-pointer transition-colors animate-pulse select-none active:scale-95"
                      >
                        <Microphone size={16} weight="fill" />
                        Dừng ghi âm
                      </button>
                    ) : (
                      <button
                        onClick={startRecording}
                        className="h-10 px-4 flex items-center gap-2 border border-hairline-strong rounded-full bg-white text-sm font-medium hover:bg-surface-strong cursor-pointer transition-colors shadow-sm select-none active:scale-95"
                      >
                        <Microphone size={16} />
                        Ghi âm trực tiếp
                      </button>
                    )}
                  </div>

                  {refAudioName && (
                    <div className="flex items-center gap-2 px-3 py-1 bg-emerald-50 text-emerald-700 text-xs font-semibold rounded-full border border-emerald-200">
                      <Check size={14} /> Giọng mẫu: {refAudioName}
                    </div>
                  )}
                </div>
              )}

              {/* Action Button */}
              <div className="flex justify-end pt-2">
                <button
                  onClick={handleGenerateTts}
                  disabled={ttsLoading}
                  className="h-11 px-8 bg-primary text-white rounded-full font-medium shadow-sm hover:bg-primary-active transition-all active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none cursor-pointer flex items-center gap-2 select-none"
                >
                  {ttsLoading ? "Đang xử lý..." : "Chuyển thành giọng nói"}
                </button>
              </div>

            </div>

            {/* Audio Waveform Output */}
            {ttsAudioUrl && (
              <div className="space-y-2">
                <h3 className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80 px-1">
                  Kết quả âm thanh
                </h3>
                <WaveformPlayer url={ttsAudioUrl} />
              </div>
            )}
          </div>
        )}

        {/* ======================================================== */}
        {/* --- TAB Content: Dialogue Studio --- */}
        {/* ======================================================== */}
        {activeTab === "dialogue" && (
          <div className="space-y-6">
            <div className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] space-y-6">
              
              <div>
                <h3 className="font-semibold text-base text-ink mb-1">Thiết kế Đoạn Hội thoại (Podcast Studio)</h3>
                <p className="text-xs text-body text-opacity-70">
                  Tạo các dòng đối thoại liên tiếp giữa nhiều người nói với các mô hình và giọng đọc khác nhau.
                </p>
              </div>

              {/* Script rows list */}
              <div className="space-y-4 divide-y divide-hairline">
                {dialogueScript.map((row, index) => (
                  <div key={index} className="pt-4 flex flex-col md:flex-row gap-4 items-start">
                    
                    {/* Index label */}
                    <div className="w-8 h-8 rounded-full bg-surface-strong border border-hairline flex items-center justify-center font-sans text-xs font-bold text-body mt-1">
                      {index + 1}
                    </div>

                    {/* Model Select */}
                    <div className="w-full md:w-44 flex-shrink-0 space-y-1">
                      <select
                        value={row.model}
                        onChange={(e) => updateDialogueRow(index, "model", e.target.value)}
                        className="w-full h-10 px-2.5 border border-hairline-strong rounded-xl outline-none bg-white text-xs focus:border-ink transition-colors cursor-pointer"
                      >
                        <option value="piper">Piper ONNX</option>
                        <option value="vieneu">VieNeu-TTS</option>
                        <option value="viterbox">Viterbox</option>
                      </select>

                      {/* Voice Select */}
                      <select
                        value={row.voice}
                        onChange={(e) => updateDialogueRow(index, "voice", e.target.value)}
                        className="w-full h-10 px-2.5 border border-hairline-strong rounded-xl outline-none bg-white text-xs focus:border-ink transition-colors cursor-pointer"
                      >
                        {voicesByModel[row.model]?.map((v) => (
                          <option key={v.id} value={v.id}>
                            {v.name.replace(" (Preset)", "").replace(" (LoRA)", "")}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Text input */}
                    <div className="flex-1 w-full">
                      <textarea
                        value={row.text}
                        onChange={(e) => updateDialogueRow(index, "text", e.target.value)}
                        placeholder="Nhập nội dung thoại..."
                        rows={2}
                        className="w-full text-sm p-3 border border-hairline-strong rounded-xl outline-none focus:border-ink transition-colors resize-none"
                      />
                    </div>

                    {/* Delete button */}
                    <button
                      onClick={() => removeDialogueRow(index)}
                      className="p-2 border border-hairline text-red-500 rounded-full hover:bg-red-50 transition-colors cursor-pointer mt-1"
                    >
                      <Trash size={16} />
                    </button>
                  </div>
                ))}
              </div>

              {/* Action row */}
              <div className="flex items-center justify-between border-t border-hairline pt-4">
                <button
                  onClick={addDialogueRow}
                  className="h-10 px-4 border border-hairline-strong rounded-full text-xs font-semibold hover:bg-surface-strong transition-colors cursor-pointer flex items-center gap-1.5 active:scale-95"
                >
                  <Plus size={14} /> Thêm câu thoại
                </button>

                <button
                  onClick={handleGenerateDialogue}
                  disabled={dialogueLoading}
                  className="h-11 px-8 bg-primary text-white rounded-full font-medium shadow-sm hover:bg-primary-active transition-all active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none cursor-pointer flex items-center gap-2 select-none"
                >
                  {dialogueLoading ? "Đang xử lý..." : "Xuất bản Hội thoại"}
                </button>
              </div>

            </div>

            {/* Audio Waveform Output */}
            {dialogueAudioUrl && (
              <div className="space-y-2">
                <h3 className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80 px-1">
                  Kết quả âm thanh
                </h3>
                <WaveformPlayer url={dialogueAudioUrl} />
              </div>
            )}
          </div>
        )}

        {/* ======================================================== */}
        {/* --- TAB Content: Meme Dubbing --- */}
        {/* ======================================================== */}
        {activeTab === "meme" && (
          <div className="space-y-6">
            
            {/* Grid of video templates */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {memesList.map((m) => (
                <div
                  key={m.id}
                  onClick={() => {
                    setSelectedMeme(m.id);
                    setDubbedVideoUrl("");
                  }}
                  className={`border cursor-pointer rounded-xl p-4 transition-all duration-200 ${
                    selectedMeme === m.id
                      ? "border-primary bg-white shadow-sm ring-1 ring-primary/20 scale-[1.02]"
                      : "border-hairline bg-white hover:border-hairline-strong"
                  }`}
                >
                  <div className={`w-full h-24 rounded-lg flex items-center justify-center ${m.color} mb-3`}>
                    <Video size={36} className="text-body text-opacity-60" />
                  </div>
                  <h4 className="font-semibold text-sm text-ink">{m.name}</h4>
                  <p className="text-xs text-body text-opacity-70 mt-1">{m.description}</p>
                </div>
              ))}
            </div>

            {/* Control Panel */}
            <div className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] space-y-6">
              
              <div className="space-y-2">
                <label className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80">
                  Câu thoại phụ đề cho Video
                </label>
                <textarea
                  value={memeText}
                  onChange={(e) => setMemeText(e.target.value)}
                  placeholder="Nhập nội dung thoại..."
                  rows={2}
                  className="w-full text-sm p-3 border border-hairline-strong rounded-xl outline-none focus:border-ink transition-colors resize-none"
                />
              </div>

              {/* Models & Voices selections */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80">
                    Mô hình giọng nói
                  </label>
                  <select
                    value={memeModel}
                    onChange={(e) => setMemeModel(e.target.value)}
                    className="w-full h-11 px-3 border border-hairline-strong rounded-xl outline-none bg-white font-sans text-sm focus:border-ink transition-colors cursor-pointer"
                  >
                    <option value="piper">Piper ONNX</option>
                    <option value="vieneu">VieNeu-TTS</option>
                    <option value="viterbox">Viterbox</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80">
                    Giọng lồng tiếng
                  </label>
                  <select
                    value={memeVoice}
                    onChange={(e) => setMemeVoice(e.target.value)}
                    className="w-full h-11 px-3 border border-hairline-strong rounded-xl outline-none bg-white font-sans text-sm focus:border-ink transition-colors cursor-pointer"
                  >
                    {voicesByModel[memeModel]?.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name.replace(" (Preset)", "").replace(" (LoRA)", "")}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Generate dubbing button */}
              <div className="flex justify-end pt-2">
                <button
                  onClick={handleGenerateDubbing}
                  disabled={dubbingLoading}
                  className="h-11 px-8 bg-primary text-white rounded-full font-medium shadow-sm hover:bg-primary-active transition-all active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none cursor-pointer flex items-center gap-2 select-none"
                >
                  {dubbingLoading ? "Đang ghép tiếng..." : "Bắt đầu lồng tiếng"}
                </button>
              </div>

            </div>

            {/* Video Player Output */}
            {dubbedVideoUrl && (
              <div className="space-y-2">
                <h3 className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80 px-1">
                  Kết quả Video đã Lồng tiếng
                </h3>
                <div className="border border-hairline rounded-xl overflow-hidden bg-black shadow-sm flex justify-center max-w-2xl mx-auto">
                  <video controls className="w-full h-auto" src={dubbedVideoUrl} />
                </div>
              </div>
            )}

          </div>
        )}

        {/* ======================================================== */}
        {/* --- TAB Content: Model Benchmark --- */}
        {/* ======================================================== */}
        {activeTab === "benchmark" && (
          <div className="space-y-6">
            
            {/* Input benchmark panel */}
            <div className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] space-y-4">
              <div className="space-y-2">
                <label className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80">
                  Câu văn thử nghiệm đồng thời
                </label>
                <textarea
                  value={benchmarkText}
                  onChange={(e) => setBenchmarkText(e.target.value)}
                  placeholder="Nhập văn bản cần so sánh..."
                  rows={2}
                  className="w-full text-sm p-3 border border-hairline-strong rounded-xl outline-none focus:border-ink transition-colors resize-none"
                />
              </div>

              <div className="flex justify-end">
                <button
                  onClick={handleRunBenchmark}
                  disabled={benchmarkLoading}
                  className="h-11 px-8 bg-primary text-white rounded-full font-medium shadow-sm hover:bg-primary-active transition-all active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none cursor-pointer flex items-center gap-2 select-none"
                >
                  {benchmarkLoading ? "Đang chạy thử nghiệm..." : "Chạy thử và So sánh"}
                </button>
              </div>
            </div>

            {/* Visual Comparative cards */}
            {benchmarkResults && (
              <div className="space-y-4">
                <h3 className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80 px-1">
                  Kết quả So sánh Hiệu năng (CPU-Only VPS)
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {benchmarkResults.map((item, idx) => (
                    <div key={idx} className="bg-white border border-hairline rounded-xl p-5 shadow-sm space-y-4 flex flex-col justify-between">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold text-sm text-ink">{item.model}</h4>
                          <span className="px-2 py-0.5 text-[9px] uppercase tracking-wider font-bold rounded-full bg-surface-strong border border-hairline-strong text-body">
                            {item.type.includes("Baseline") ? "Light" : "Heavy"}
                          </span>
                        </div>
                        <p className="text-xs text-body text-opacity-70">{item.type}</p>
                      </div>

                      <div className="space-y-2 border-t border-b border-hairline py-3 my-2 font-sans">
                        <div className="flex justify-between text-xs">
                          <span className="text-body">Độ trễ xử lý (Latency)</span>
                          <span className="font-semibold text-ink">{item.latency.toFixed(2)}s</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-body">Hệ số RTF (Sinh/Giây)</span>
                          <span className="font-semibold text-ink">{item.rtf.toFixed(2)}x</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-body">Tải bộ nhớ (RAM)</span>
                          <span className="font-semibold text-ink">{item.ram}</span>
                        </div>
                        {item.mos && (
                          <div className="flex justify-between text-xs items-center mt-1 pt-2 border-t border-hairline border-opacity-50">
                            <span className="text-body" title="Mean Opinion Score (Tự nhiên, Rõ ràng, Ổn định)">MOS Score</span>
                            <div className="flex items-center gap-2">
                              <div className="w-16 h-1.5 bg-surface-strong rounded-full overflow-hidden">
                                <div className="h-full bg-primary" style={{ width: `${(item.mos.overall / 5) * 100}%` }} />
                              </div>
                              <span className="font-semibold text-ink">{item.mos.overall}/5</span>
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="pt-2">
                        <audio controls src={item.audio_url} className="w-full h-8" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        )}

        {/* ======================================================== */}
        {/* --- TAB Content: A/B Blind Test --- */}
        {/* ======================================================== */}
        {activeTab === "ab_test" && (
          <div className="space-y-6">
            <div className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] space-y-6">
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Config Model A */}
                <div className="space-y-4 p-4 border border-hairline-strong rounded-xl bg-surface-strong/20">
                  <h4 className="font-semibold text-sm text-ink">Cấu hình Mẫu A</h4>
                  <div className="space-y-2">
                    <label className="text-[10px] uppercase tracking-wider font-semibold text-body">Mô hình</label>
                    <select
                      value={abModels.modelA}
                      onChange={e => setAbModels({...abModels, modelA: e.target.value, voiceA: voicesByModel[e.target.value][0].id})}
                      className="w-full h-10 px-3 border border-hairline-strong rounded-xl outline-none text-sm"
                    >
                      <option value="piper">Piper (Lightweight)</option>
                      <option value="viterbox">Viterbox (Flow-matching)</option>
                      <option value="vieneu">VieNeu-TTS (LoRA)</option>
                      <option value="vieneu_base">VieNeu-TTS (Base - Zero-shot)</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] uppercase tracking-wider font-semibold text-body">Giọng đọc</label>
                    <select
                      value={abModels.voiceA}
                      onChange={e => setAbModels({...abModels, voiceA: e.target.value})}
                      className="w-full h-10 px-3 border border-hairline-strong rounded-xl outline-none text-sm"
                    >
                      {voicesByModel[abModels.modelA]?.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
                    </select>
                  </div>
                  {/* Upload UI for Model A if Viterbox or Zero-shot */}
                  {(abModels.modelA === "viterbox" || abModels.modelA.startsWith("vieneu")) && (
                    <div className="pt-2">
                      <label className="h-8 px-3 flex justify-center items-center gap-2 border border-dashed border-hairline-strong rounded-lg bg-white text-xs font-medium hover:bg-surface-strong cursor-pointer transition-colors shadow-sm text-body">
                        <Upload size={14} />
                        {abRefAudioA ? abRefAudioA.name : "Tải lên Audio mẫu Zero-Shot (Tùy chọn)"}
                        <input type="file" accept="audio/*" className="hidden" onChange={e => setAbRefAudioA(e.target.files[0])} />
                      </label>
                    </div>
                  )}
                </div>

                {/* Config Model B */}
                <div className="space-y-4 p-4 border border-hairline-strong rounded-xl bg-surface-strong/20">
                  <h4 className="font-semibold text-sm text-ink">Cấu hình Mẫu B</h4>
                  <div className="space-y-2">
                    <label className="text-[10px] uppercase tracking-wider font-semibold text-body">Mô hình</label>
                    <select
                      value={abModels.modelB}
                      onChange={e => setAbModels({...abModels, modelB: e.target.value, voiceB: voicesByModel[e.target.value][0].id})}
                      className="w-full h-10 px-3 border border-hairline-strong rounded-xl outline-none text-sm"
                    >
                      <option value="piper">Piper (Lightweight)</option>
                      <option value="viterbox">Viterbox (Flow-matching)</option>
                      <option value="vieneu">VieNeu-TTS (LoRA)</option>
                      <option value="vieneu_base">VieNeu-TTS (Base - Zero-shot)</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] uppercase tracking-wider font-semibold text-body">Giọng đọc</label>
                    <select
                      value={abModels.voiceB}
                      onChange={e => setAbModels({...abModels, voiceB: e.target.value})}
                      className="w-full h-10 px-3 border border-hairline-strong rounded-xl outline-none text-sm"
                    >
                      {voicesByModel[abModels.modelB]?.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
                    </select>
                  </div>
                  {/* Upload UI for Model B if Viterbox or Zero-shot */}
                  {(abModels.modelB === "viterbox" || abModels.modelB.startsWith("vieneu")) && (
                    <div className="pt-2">
                      <label className="h-8 px-3 flex justify-center items-center gap-2 border border-dashed border-hairline-strong rounded-lg bg-white text-xs font-medium hover:bg-surface-strong cursor-pointer transition-colors shadow-sm text-body">
                        <Upload size={14} />
                        {abRefAudioB ? abRefAudioB.name : "Tải lên Audio mẫu Zero-Shot (Tùy chọn)"}
                        <input type="file" accept="audio/*" className="hidden" onChange={e => setAbRefAudioB(e.target.files[0])} />
                      </label>
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-hairline">
                <label className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80">
                  Câu văn đánh giá
                </label>
                <textarea
                  value={abText}
                  onChange={(e) => setAbText(e.target.value)}
                  placeholder="Nhập văn bản..."
                  rows={2}
                  className="w-full text-sm p-3 border border-hairline-strong rounded-xl outline-none focus:border-ink transition-colors resize-none"
                />
              </div>

              <div className="flex justify-end">
                <button
                  onClick={handleRunAbTest}
                  disabled={abLoading}
                  className="h-11 px-8 bg-primary text-white rounded-full font-medium shadow-sm hover:bg-primary-active transition-all active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none cursor-pointer flex items-center gap-2 select-none"
                >
                  {abLoading ? "Đang tạo ẩn danh..." : "Bắt đầu A/B Test"}
                </button>
              </div>
            </div>

            {abResults && (
              <div className="space-y-4">
                <h3 className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80 px-1 text-center">
                  Vui lòng nghe và chọn mẫu bạn thấy tự nhiên hơn
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] flex flex-col items-center gap-4">
                    <h4 className="font-semibold text-lg text-ink">Mẫu A</h4>
                    <audio controls src={abResults.sample1} className="w-full" />
                    <button
                      onClick={() => handleAbVote(1)}
                      disabled={!!abVoteResult}
                      className="w-full h-11 border border-primary text-primary rounded-xl font-medium hover:bg-primary/5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                    >
                      Bình chọn Mẫu A
                    </button>
                  </div>
                  
                  <div className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] flex flex-col items-center gap-4">
                    <h4 className="font-semibold text-lg text-ink">Mẫu B</h4>
                    <audio controls src={abResults.sample2} className="w-full" />
                    <button
                      onClick={() => handleAbVote(2)}
                      disabled={!!abVoteResult}
                      className="w-full h-11 border border-primary text-primary rounded-xl font-medium hover:bg-primary/5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                    >
                      Bình chọn Mẫu B
                    </button>
                  </div>
                </div>

                {abVoteResult && (
                  <div className="mt-6 p-6 bg-emerald-50 border border-emerald-200 rounded-xl text-center space-y-2 animate-in fade-in duration-500">
                    <h3 className="font-bold text-emerald-800 text-lg">Cảm ơn bạn đã bình chọn!</h3>
                    <p className="text-sm text-emerald-700">
                      Bạn đã chọn <strong>{abVoteResult.winnerInfo}</strong>.
                    </p>
                    <p className="text-xs text-emerald-600 mt-2">
                      Sự thật: Mẫu A là <strong>{abResults.modelsInfo[1]}</strong>, Mẫu B là <strong>{abResults.modelsInfo[2]}</strong>.<br/>
                      Giọng bạn chọn thuộc về mô hình: <strong className="uppercase">{abVoteResult.winnerModel}</strong>.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ======================================================== */}
        {/* --- TAB Content: Pronunciation Editor --- */}
        {/* ======================================================== */}
        {activeTab === "pronunciation" && (
          <div className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] space-y-6">
            <div className="space-y-1">
              <h3 className="font-semibold text-base text-ink">Từ điển Phát âm Tùy chỉnh</h3>
              <p className="text-xs text-body text-opacity-70">
                Chỉnh sửa cách đọc của các từ đặc biệt (từ viết tắt, tiếng lóng) trước khi đưa vào mô hình TTS.
              </p>
            </div>

            <div className="flex gap-2 items-end">
              <div className="flex-1 space-y-1">
                <label className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80">
                  Từ gốc (Ví dụ: ko)
                </label>
                <input
                  type="text"
                  value={newPronun.original}
                  onChange={e => setNewPronun({...newPronun, original: e.target.value})}
                  className="w-full h-10 px-3 border border-hairline-strong rounded-xl outline-none text-sm focus:border-ink transition-colors"
                />
              </div>
              <div className="flex-1 space-y-1">
                <label className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80">
                  Phát âm (Ví dụ: không)
                </label>
                <input
                  type="text"
                  value={newPronun.replacement}
                  onChange={e => setNewPronun({...newPronun, replacement: e.target.value})}
                  className="w-full h-10 px-3 border border-hairline-strong rounded-xl outline-none text-sm focus:border-ink transition-colors"
                />
              </div>
              <button
                onClick={handleAddPronun}
                className="h-10 px-6 bg-ink text-white rounded-xl text-sm font-medium hover:bg-black transition-colors cursor-pointer active:scale-95 shadow-sm"
              >
                Thêm
              </button>
            </div>

            <div className="border border-hairline rounded-xl overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead className="bg-surface-strong">
                  <tr>
                    <th className="px-4 py-3 font-semibold text-body text-xs uppercase tracking-wider">Từ Gốc</th>
                    <th className="px-4 py-3 font-semibold text-body text-xs uppercase tracking-wider">Phát Âm Thay Thế</th>
                    <th className="px-4 py-3 font-semibold text-body text-xs uppercase tracking-wider w-20 text-center">Xóa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-hairline">
                  {pronunciationDict.length === 0 ? (
                    <tr><td colSpan="3" className="px-4 py-8 text-center text-body text-opacity-60 text-xs">Chưa có từ nào trong từ điển.</td></tr>
                  ) : pronunciationDict.map((item, idx) => (
                    <tr key={idx} className="hover:bg-surface transition-colors">
                      <td className="px-4 py-3 text-ink font-medium">{item.original}</td>
                      <td className="px-4 py-3 text-body">{item.replacement}</td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => handleDeletePronun(item.original)}
                          className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
                        >
                          <Trash size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* --- TAB Content: AI Chat Partner --- */}
        {/* ======================================================== */}
        {activeTab === "chat" && (
          <div className="space-y-6">
            <div className="flex justify-center mb-4">
              <div className="bg-white border border-hairline p-1 flex rounded-full shadow-sm">
                <button
                  onClick={() => setChatMode("single")}
                  className={`px-6 py-2 text-sm font-semibold rounded-full transition-all ${
                    chatMode === "single" ? "bg-primary text-white shadow" : "text-body hover:bg-surface-strong"
                  }`}
                >
                  Trò chuyện cá nhân (1 AI)
                </button>
                <button
                  onClick={() => setChatMode("pair")}
                  className={`px-6 py-2 text-sm font-semibold rounded-full transition-all ${
                    chatMode === "pair" ? "bg-primary text-white shadow" : "text-body hover:bg-surface-strong"
                  }`}
                >
                  Đạo diễn hội thoại (2 AI)
                </button>
              </div>
            </div>

            {chatMode === "single" && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-start">
                {/* Sidebar list of characters */}
                <div className="md:col-span-1 space-y-3">
                  <h3 className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body text-opacity-80 px-1">
                    Đối tác Trò chuyện
                  </h3>
                  <div className="flex md:flex-col gap-2 overflow-x-auto pb-2 md:pb-0 scrollbar-none">
                    {characters.map((char) => (
                      <button
                        key={char.id}
                        onClick={() => {
                          if (!chatLoading) {
                            setActiveChar(char);
                          }
                        }}
                        disabled={chatLoading}
                        className={`w-full text-left px-4 py-3 border rounded-xl flex items-center gap-3 transition-all duration-200 cursor-pointer ${
                          activeChar.id === char.id
                            ? "border-primary bg-white shadow-sm ring-1 ring-primary/20 scale-[1.02]"
                            : "border-hairline bg-white hover:border-hairline-strong"
                        }`}
                      >
                        <div className={`w-8 h-8 rounded-full ${char.color}/20 text-ink text-xs font-bold flex items-center justify-center`}>
                          {char.name[0]}
                        </div>
                        <div className="min-w-0">
                          <h4 className="font-semibold text-xs text-ink truncate">{char.name}</h4>
                          <p className="text-[10px] text-body text-opacity-70 truncate">{char.desc}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Chat Room */}
                <div className="md:col-span-3 flex flex-col h-[550px] bg-white border border-hairline rounded-xl shadow-sm overflow-hidden">
                  
                  {/* Chat Header */}
                  <div className="px-5 py-4 border-b border-hairline bg-canvas-soft flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-full ${activeChar.color}/20 text-ink font-bold flex items-center justify-center`}>
                        {activeChar.name[0]}
                      </div>
                      <div>
                        <h3 className="font-semibold text-sm text-ink">{activeChar.name}</h3>
                        <p className="text-[10px] text-body text-opacity-70">
                          Đóng vai bởi {activeChar.model === "vieneu" ? "VieNeu-TTS" : "Viterbox"}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Chat Messages */}
                  <div className="flex-1 p-5 overflow-y-auto space-y-4 bg-[#faf9f6]/40">
                    {chatHistory.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-[70%] px-4 py-3 rounded-2xl text-sm shadow-sm ${
                            msg.role === "user"
                              ? "bg-primary text-white rounded-br-none"
                              : "bg-white border border-hairline text-ink rounded-bl-none"
                          }`}
                        >
                          {msg.content}
                        </div>
                      </div>
                    ))}
                    
                    {chatLoading && (
                      <div className="flex justify-start">
                        <div className="bg-white border border-hairline px-4 py-3 rounded-2xl rounded-bl-none text-xs text-body text-opacity-60 shadow-sm flex items-center gap-2">
                          <div className="w-1.5 h-1.5 bg-body rounded-full animate-bounce" />
                          <div className="w-1.5 h-1.5 bg-body rounded-full animate-bounce [animation-delay:0.2s]" />
                          <div className="w-1.5 h-1.5 bg-body rounded-full animate-bounce [animation-delay:0.4s]" />
                          Đang trả lời & sinh giọng nói...
                        </div>
                      </div>
                    )}
                    
                    <div ref={chatBottomRef} />
                  </div>

                  {/* Spoken output waveform (if any) */}
                  {chatAudioUrl && (
                    <div className="px-5 py-2 border-t border-hairline bg-canvas-soft flex items-center gap-3">
                      <span className="text-[10px] uppercase tracking-wider font-semibold text-body select-none">
                        Phát lại thoại
                      </span>
                      <div className="flex-1">
                        <audio controls src={chatAudioUrl} className="w-full h-8" />
                      </div>
                    </div>
                  )}

                  {/* Chat input box */}
                  <div className="p-4 border-t border-hairline flex gap-2">
                    <input
                      type="text"
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleSendChatMessage()}
                      disabled={chatLoading}
                      placeholder={`Trò chuyện với ${activeChar.name}...`}
                      className="flex-1 h-11 px-4 border border-hairline-strong rounded-xl outline-none text-sm focus:border-ink transition-colors placeholder-stone-400 disabled:opacity-50"
                    />
                    <button
                      onClick={handleSendChatMessage}
                      disabled={chatLoading || !chatInput.trim()}
                      className="h-11 px-6 bg-primary text-white rounded-xl text-sm font-medium hover:bg-primary-active transition-all shadow-sm active:scale-95 disabled:opacity-50 disabled:pointer-events-none cursor-pointer flex items-center justify-center select-none"
                    >
                      Gửi
                    </button>
                  </div>
                </div>
              </div>
            )}

            {chatMode === "pair" && (
              <div className="bg-white border border-hairline rounded-xl shadow-sm p-6 max-w-5xl mx-auto space-y-6">
                <div className="text-center space-y-1 mb-4">
                  <h3 className="font-semibold text-lg text-ink">Sân khấu Đàm thoại 2 AI</h3>
                  <p className="text-sm text-body text-opacity-70">
                    Cung cấp một chủ đề và chọn 2 nhân vật, hệ thống sẽ đạo diễn một cuộc trò chuyện ngắn giữa họ.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Select Char A */}
                  <div className="space-y-2 p-4 border border-hairline-strong bg-surface-strong/20 rounded-xl">
                    <label className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body">
                      Nhân vật A
                    </label>
                    <select
                      value={pairCharA.id}
                      onChange={(e) => setPairCharA(characters.find(c => c.id === e.target.value))}
                      className="w-full h-11 px-3 border border-hairline-strong rounded-xl outline-none bg-white font-sans text-sm"
                    >
                      {characters.map(c => <option key={`A_${c.id}`} value={c.id}>{c.name}</option>)}
                    </select>
                  </div>
                  {/* Select Char B */}
                  <div className="space-y-2 p-4 border border-hairline-strong bg-surface-strong/20 rounded-xl">
                    <label className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body">
                      Nhân vật B
                    </label>
                    <select
                      value={pairCharB.id}
                      onChange={(e) => setPairCharB(characters.find(c => c.id === e.target.value))}
                      className="w-full h-11 px-3 border border-hairline-strong rounded-xl outline-none bg-white font-sans text-sm"
                    >
                      {characters.map(c => <option key={`B_${c.id}`} value={c.id}>{c.name}</option>)}
                    </select>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-[11px] uppercase tracking-wider font-semibold font-sans text-body">
                    Chủ đề thảo luận
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={pairTopic}
                      onChange={(e) => setPairTopic(e.target.value)}
                      placeholder="Ví dụ: Ăn sáng ở Hà Nội hay Sài Gòn ngon hơn?"
                      className="flex-1 h-11 px-4 border border-hairline-strong rounded-xl outline-none text-sm focus:border-ink"
                    />
                    <button
                      onClick={handleGeneratePairChat}
                      disabled={pairLoading}
                      className="h-11 px-6 bg-ink text-white rounded-xl text-sm font-medium hover:bg-black transition-colors cursor-pointer active:scale-95 shadow-sm disabled:opacity-50"
                    >
                      {pairLoading ? "Đang đạo diễn..." : "Bắt đầu diễn"}
                    </button>
                  </div>
                </div>

                {/* Display Dialogue */}
                {(pairDialogue.length > 0 || pairLoading) && (
                  <div className="mt-8 p-5 border border-hairline rounded-xl bg-[#faf9f6]/40 min-h-[300px] overflow-y-auto max-h-[500px]">
                    {pairLoading ? (
                      <div className="flex justify-center items-center h-full text-sm text-body text-opacity-60 gap-2">
                        <div className="w-2 h-2 bg-body rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-body rounded-full animate-bounce [animation-delay:0.2s]" />
                        <div className="w-2 h-2 bg-body rounded-full animate-bounce [animation-delay:0.4s]" />
                        Đang viết kịch bản & tổng hợp giọng nói...
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {pairDialogue.map((line, idx) => {
                          const isCharA = line.character === pairCharA.id;
                          const charInfo = isCharA ? pairCharA : pairCharB;
                          const isPlaying = currentPlayingIndex === idx;

                          return (
                            <div key={idx} className={`flex ${isCharA ? "justify-start" : "justify-end"}`}>
                              <div className={`max-w-[70%] flex gap-3 ${isCharA ? "flex-row" : "flex-row-reverse"}`}>
                                <div className={`w-10 h-10 shrink-0 rounded-full ${charInfo.color}/20 text-ink font-bold flex items-center justify-center border border-hairline relative`}>
                                  {charInfo.name[0]}
                                  {isPlaying && (
                                    <span className="absolute -top-1 -right-1 flex h-3 w-3">
                                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                                      <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
                                    </span>
                                  )}
                                </div>
                                <div className={`p-4 rounded-2xl text-sm shadow-sm ${isCharA ? "bg-white border border-hairline rounded-tl-none" : "bg-primary text-white rounded-tr-none"}`}>
                                  <p className="font-semibold text-xs mb-1 opacity-80">{charInfo.name}</p>
                                  <p>{line.text}</p>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                        <div ref={chatBottomRef} />
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        </div>
      </main>

    </div>
  );
}
