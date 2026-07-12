import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Create figures directory if it doesn't exist
os.makedirs("figures", exist_ok=True)

# Set font styling
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans']
plt.rcParams['axes.edgecolor'] = '#CCCCCC'
plt.rcParams['axes.linewidth'] = 0.8

# Color Palette (Elegant and modern)
COLOR_PRIMARY = '#1F77B4'    # Elegant Blue
COLOR_SECONDARY = '#FF7F0E'  # Elegant Orange
COLOR_SUCCESS = '#2CA02C'    # Soft Green
COLOR_WARNING = '#D62728'    # Soft Red
COLOR_NEUTRAL = '#7F7F7F'    # Gray
COLOR_BG = '#F5F5F5'         # Light Gray Background

# ==========================================
# 4. DATA SPLIT PIE CHART (Figure 4)
# ==========================================
def draw_data_split():
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    sizes = [1476, 77]
    labels = ['Train (1476 mẫu)', 'Validation (77 mẫu)']
    colors = ['#1F77B4', '#FF7F0E']
    
    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%',
        startangle=140, 
        colors=colors,
        textprops=dict(color="black", fontsize=11, weight="bold"),
        wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2)  # Donut chart
    )
    
    # Customize text properties
    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_color('white')
        
    ax.set_title("Tỉ lệ phân chia dữ liệu Train/Validation\n(Tổng cộng: 1553 mẫu sạch)", fontsize=13, weight="bold", pad=20)
    plt.tight_layout()
    plt.savefig("figures/data_split_pie.png", bbox_inches='tight')
    plt.savefig("figures/data_split_pie.pdf", bbox_inches='tight')
    plt.close()
    print("Generated figures/data_split_pie.png and .pdf")

# ==========================================
# 6. LOSS CURVE (Figure 6)
# ==========================================
def draw_loss_curve():
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
    
    steps = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500]
    train_loss = [0.574547, 0.557997, 0.544064, 0.546009, 0.528937, 0.514483, 0.507884, 0.497415, 0.488952, 0.487707, 0.463686, 0.456464, 0.450108, 0.448146, 0.422112]
    val_loss = [0.589996, 0.580803, 0.578641, 0.578091, 0.580356, 0.583667, 0.588822, 0.593953, 0.601543, 0.610968, 0.620215, 0.630315, 0.639363, 0.650970, 0.656436]

    ax.plot(steps, train_loss, label='Training Loss', color='#1F77B4', marker='o', markersize=4, linewidth=2)
    ax.plot(steps, val_loss, label='Validation Loss', color='#FF7F0E', marker='o', markersize=4, linewidth=2)
    
    # Highlight optimal checkpoint region
    ax.axvline(x=400, color='#2CA02C', linestyle='--', linewidth=1.5, label='Điểm tối ưu (Step 400)')
    ax.axvspan(300, 500, alpha=0.15, color='#2CA02C')
    
    ax.text(430, 0.63, 'Vùng tối ưu\n(Step 300 - 500)', color='#2CA02C', fontsize=9, weight='bold')
    ax.text(1050, 0.59, 'Overfitting Area\n(Validation Loss tăng)', color='#D62728', fontsize=9, weight='bold')
    
    ax.set_xlabel('Huấn luyện Steps', fontsize=11, labelpad=8)
    ax.set_ylabel('Loss (Cross-Entropy)', fontsize=11, labelpad=8)
    ax.set_title('Đường cong Loss huấn luyện LoRA cho VieNeu-0.3B', fontsize=12, weight='bold', pad=15)
    ax.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#E0E0E0')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_xlim(50, 1550)
    ax.set_ylim(0.40, 0.68)
    
    plt.tight_layout()
    plt.savefig("figures/loss_curve.png", bbox_inches='tight')
    plt.savefig("figures/loss_curve.pdf", bbox_inches='tight')
    plt.close()
    print("Generated figures/loss_curve.png and .pdf")

# ==========================================
# 7. MODEL COMPARISON BAR CHART (Figure 7)
# ==========================================
def draw_model_comparison():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), dpi=300)
    
    models = ['Viterbox', 'VieNeu Base', 'VieNeu LoRA']
    sim_scores = [0.0971, 0.1249, 0.1378]
    wer_scores = [1.9384, 2.5725, 12.7442]
    
    # Plot 1: Speaker Similarity (Higher is better)
    bars1 = ax1.bar(models, sim_scores, color=['#7F7F7F', '#1F77B4', '#FF7F0E'], width=0.5, edgecolor='black', linewidth=0.7)
    ax1.set_ylabel('Speaker Cosine Similarity (↑)', fontsize=11, labelpad=8)
    ax1.set_title('Độ tương đồng giọng nói (Similarity)', fontsize=11, weight='bold', pad=12)
    ax1.set_ylim(0, 0.18)
    ax1.grid(axis='y', linestyle=':', alpha=0.6)
    
    # Add values on top of bars
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.005, f"{yval:.4f}", ha='center', va='bottom', fontsize=9, weight='bold')
        
    # Plot 2: WER (Lower is better)
    bars2 = ax2.bar(models, wer_scores, color=['#7F7F7F', '#1F77B4', '#D62728'], width=0.5, edgecolor='black', linewidth=0.7)
    ax2.set_ylabel('Word Error Rate - WER (↓)', fontsize=11, labelpad=8)
    ax2.set_title('Tỉ lệ lỗi từ (WER)', fontsize=11, weight='bold', pad=12)
    ax2.set_ylim(0, 15.0)
    ax2.grid(axis='y', linestyle=':', alpha=0.6)
    
    # Add values on top of bars
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 0.3, f"{yval:.4f}", ha='center', va='bottom', fontsize=9, weight='bold')
        
    plt.suptitle('So sánh hiệu năng 3 mô hình trên 146 mẫu Test unseen', fontsize=13, weight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig("figures/model_comparison.png", bbox_inches='tight')
    plt.savefig("figures/model_comparison.pdf", bbox_inches='tight')
    plt.close()
    print("Generated figures/model_comparison.png and .pdf")

# ==========================================
# 1. TTS ARCHITECTURE COMPARISON DIAGRAM (Figure 1)
# ==========================================
def draw_tts_architecture():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5), dpi=300)
    
    # Clear axes
    for ax in [ax1, ax2]:
        ax.axis('off')
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        
    # Panel 1: Non-autoregressive (Viterbox / VITS)
    ax1.set_title("Hướng Non-Autoregressive (VITS / Viterbox)", fontsize=11, weight='bold', pad=10, color='#333333')
    # Draw boxes
    ax1.add_patch(patches.FancyBboxPatch((1, 8), 8, 1, boxstyle="round,pad=0.2", facecolor='#E3F2FD', edgecolor='#1E88E5', linewidth=1.5))
    ax1.text(5, 8.5, "Văn bản đầu vào (Text)", ha='center', va='center', fontsize=10, weight='bold')
    
    ax1.add_patch(patches.FancyBboxPatch((1, 5.5), 5, 1, boxstyle="round,pad=0.2", facecolor='#F3E5F5', edgecolor='#8E24AA', linewidth=1.5))
    ax1.text(3.5, 6, "Acoustic / Flow Model\n(Parallel Generation)", ha='center', va='center', fontsize=9, weight='bold')
    
    ax1.add_patch(patches.FancyBboxPatch((7, 5.5), 2, 1, boxstyle="round,pad=0.2", facecolor='#FFF3E0', edgecolor='#FB8C00', linewidth=1.5))
    ax1.text(8, 6, "Speaker\nEmbedding", ha='center', va='center', fontsize=8, weight='bold')
    
    ax1.add_patch(patches.FancyBboxPatch((1, 3), 8, 1, boxstyle="round,pad=0.2", facecolor='#E8F5E9', edgecolor='#43A047', linewidth=1.5))
    ax1.text(5, 3.5, "Decoder / Vocoder (Mel -> Waveform)", ha='center', va='center', fontsize=10, weight='bold')
    
    ax1.add_patch(patches.FancyBboxPatch((1, 0.5), 8, 1, boxstyle="round,pad=0.2", facecolor='#FFE0B2', edgecolor='#F57C00', linewidth=1.5))
    ax1.text(5, 1, "Âm thanh đầu ra (Waveform - Rất nhanh)", ha='center', va='center', fontsize=10, weight='bold')
    
    # Arrows Panel 1
    # text -> acoustic
    ax1.annotate('', xy=(3.5, 6.7), xytext=(3.5, 7.8), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    # speaker -> acoustic
    ax1.annotate('', xy=(5.8, 6.0), xytext=(6.8, 6.0), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    # acoustic -> decoder (also needs arrow from text box to cover the width)
    ax1.annotate('', xy=(5, 4.2), xytext=(5, 5.3), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    # decoder -> output
    ax1.annotate('', xy=(5, 1.7), xytext=(5, 2.8), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    
    # Panel 2: Autoregressive (VieNeu)
    ax2.set_title("Hướng Autoregressive (VieNeu-0.3B)", fontsize=11, weight='bold', pad=10, color='#333333')
    
    ax2.add_patch(patches.FancyBboxPatch((1, 8.5), 4, 0.8, boxstyle="round,pad=0.15", facecolor='#E3F2FD', edgecolor='#1E88E5', linewidth=1.5))
    ax2.text(3, 8.9, "Văn bản + G2P\n(Phonemes)", ha='center', va='center', fontsize=8, weight='bold')
    
    ax2.add_patch(patches.FancyBboxPatch((5.5, 8.5), 3.5, 0.8, boxstyle="round,pad=0.15", facecolor='#FFF3E0', edgecolor='#FB8C00', linewidth=1.5))
    ax2.text(7.25, 8.9, "Giọng mồi (WAV)\n-> Codec Tokens", ha='center', va='center', fontsize=8, weight='bold')
    
    ax2.add_patch(patches.FancyBboxPatch((1, 5.5), 8, 1.5, boxstyle="round,pad=0.2", facecolor='#EDE7F6', edgecolor='#5E35B1', linewidth=1.5))
    ax2.text(5, 6.25, "Autoregressive LLM (VieNeu-0.3B)\nDự đoán Speech Code kế tiếp tuần tự\n(từng token một, có vòng lặp hồi quy)", ha='center', va='center', fontsize=9, weight='bold')
    
    ax2.add_patch(patches.FancyBboxPatch((1, 3), 8, 1, boxstyle="round,pad=0.2", facecolor='#E8F5E9', edgecolor='#43A047', linewidth=1.5))
    ax2.text(5, 3.5, "Codec Decoder (Speech Tokens -> WAV)", ha='center', va='center', fontsize=10, weight='bold')
    
    ax2.add_patch(patches.FancyBboxPatch((1, 0.5), 8, 1, boxstyle="round,pad=0.2", facecolor='#FFCDD2', edgecolor='#E53935', linewidth=1.5))
    ax2.text(5, 1, "Âm thanh đầu ra (Waveform - Suy luận chậm)", ha='center', va='center', fontsize=10, weight='bold')
    
    # Arrows Panel 2
    # text -> LLM
    ax2.annotate('', xy=(3, 7.2), xytext=(3, 8.3), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    # voice prompt -> LLM
    ax2.annotate('', xy=(7.25, 7.2), xytext=(7.25, 8.3), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    # LLM autoregressive feedback loop
    loop = patches.Arc((8.5, 6.25), 1.2, 1.5, angle=0, theta1=270, theta2=90, color='#5E35B1', lw=1.5, ls='--')
    ax2.add_patch(loop)
    ax2.annotate('', xy=(8.5, 7.0), xytext=(8.49, 7.01), arrowprops=dict(arrowstyle="->", color='#5E35B1', lw=1.5))
    ax2.text(9.2, 6.25, "Hồi quy\n(Loop)", color='#5E35B1', fontsize=7, weight='bold', va='center')
    
    # LLM -> codec decoder
    ax2.annotate('', xy=(5, 4.2), xytext=(5, 5.3), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    # decoder -> output
    ax2.annotate('', xy=(5, 1.7), xytext=(5, 2.8), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    
    plt.tight_layout()
    plt.savefig("figures/tts_architecture_comparison.png", bbox_inches='tight')
    plt.savefig("figures/tts_architecture_comparison.pdf", bbox_inches='tight')
    plt.close()
    print("Generated figures/tts_architecture_comparison.png and .pdf")

# ==========================================
# 2. LORA ARCHITECTURE DIAGRAM (Figure 2)
# ==========================================
def draw_lora_architecture():
    fig, ax = plt.subplots(figsize=(6.5, 5), dpi=300)
    ax.axis('off')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    
    # Input x
    ax.add_patch(patches.FancyBboxPatch((4, 8.5), 2, 0.8, boxstyle="round,pad=0.1", facecolor='#ECEFF1', edgecolor='#455A64', linewidth=1.5))
    ax.text(5, 8.9, "Đầu vào x\n(d_in)", ha='center', va='center', fontsize=10, weight='bold')
    
    # Left path: Frozen pre-trained weight W0
    ax.add_patch(patches.FancyBboxPatch((0.5, 4), 3, 3.5, boxstyle="round,pad=0.15", facecolor='#CFD8DC', edgecolor='#78909C', linewidth=1.5))
    ax.text(2, 5.75, "Trọng số gốc\nđóng băng\n\nW0\n(d_out x d_in)", ha='center', va='center', fontsize=10, weight='bold', color='#37474F')
    
    # Right path: Low-rank matrices A and B (trainable)
    # Matrix A
    ax.add_patch(patches.FancyBboxPatch((6, 5.8), 3.5, 1.2, boxstyle="round,pad=0.1", facecolor='#FFE0B2', edgecolor='#FB8C00', linewidth=1.5))
    ax.text(7.75, 6.4, "Ma trận giảm chiều A\n(r x d_in)\n(Trainable)", ha='center', va='center', fontsize=8.5, weight='bold')
    
    # Matrix B
    ax.add_patch(patches.FancyBboxPatch((6, 4.0), 3.5, 1.2, boxstyle="round,pad=0.1", facecolor='#FFCC80', edgecolor='#F57C00', linewidth=1.5))
    ax.text(7.75, 4.6, "Ma trận tăng chiều B\n(d_out x r)\n(Trainable)", ha='center', va='center', fontsize=8.5, weight='bold')
    
    # Summation node
    circle = patches.Circle((5, 2.2), 0.4, facecolor='#E8F5E9', edgecolor='#43A047', linewidth=1.5)
    ax.add_patch(circle)
    ax.text(5, 2.2, "+", ha='center', va='center', fontsize=16, weight='bold', color='#1B5E20')
    
    # Output y
    ax.add_patch(patches.FancyBboxPatch((4, 0.5), 2, 0.8, boxstyle="round,pad=0.1", facecolor='#E8F5E9', edgecolor='#43A047', linewidth=1.5))
    ax.text(5, 0.9, "Đầu ra h\n(d_out)", ha='center', va='center', fontsize=10, weight='bold')
    
    # Connective arrows
    # Input split left
    ax.annotate('', xy=(2, 7.7), xytext=(4, 8.9), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5, connectionstyle="angle,angleA=180,angleB=90,rad=5"))
    # Input split right
    ax.annotate('', xy=(7.75, 7.2), xytext=(6, 8.9), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5, connectionstyle="angle,angleA=0,angleB=90,rad=5"))
    
    # Matrix A -> Matrix B
    ax.annotate('', xy=(7.75, 5.3), xytext=(7.75, 5.7), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    
    # W0 -> Sum
    ax.annotate('', xy=(4.55, 2.2), xytext=(2, 3.8), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5, connectionstyle="angle,angleA=180,angleB=90,rad=5"))
    
    # B -> Sum
    ax.annotate('', xy=(5.45, 2.2), xytext=(7.75, 3.8), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5, connectionstyle="angle,angleA=0,angleB=90,rad=5"))
    
    # Sum -> Output
    ax.annotate('', xy=(5, 1.45), xytext=(5, 1.8), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    
    # Annotation text
    ax.text(2.6, 2.4, "W0 * x", fontsize=9, color='#37474F', weight='bold')
    ax.text(6.8, 2.4, "B * A * x * (alpha/r)", fontsize=9, color='#FB8C00', weight='bold', ha='right')
    ax.text(5, 9.8, "Cấu trúc Low-Rank Adaptation (LoRA)", fontsize=13, weight='bold', ha='center')
    
    plt.tight_layout()
    plt.savefig("figures/lora_architecture.png", bbox_inches='tight')
    plt.savefig("figures/lora_architecture.pdf", bbox_inches='tight')
    plt.close()
    print("Generated figures/lora_architecture.png and .pdf")

# ==========================================
# 3. ATTENTION COMPARISON DIAGRAM (Figure 3)
# ==========================================
def draw_attention_comparison():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.8), dpi=300)
    
    for ax in [ax1, ax2]:
        ax.axis('off')
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        
    # Panel 1: SDPA
    ax1.set_title("Scaled Dot-Product Attention (SDPA / Flash)", fontsize=11, weight='bold', pad=10)
    ax1.add_patch(patches.FancyBboxPatch((1, 8), 4, 1, boxstyle="round,pad=0.1", facecolor='#ECEFF1', edgecolor='#455A64', linewidth=1.2))
    ax1.text(3, 8.5, "Đầu vào Q, K, V", ha='center', va='center', fontsize=9, weight='bold')
    
    ax1.add_patch(patches.FancyBboxPatch((1, 4.5), 4, 2, boxstyle="round,pad=0.2", facecolor='#FFCDD2', edgecolor='#E53935', linewidth=1.5))
    ax1.text(3, 5.5, "SDPA Kernel Tối Ưu\n(Chạy trực tiếp trên GPU)\nKhông lưu trữ ma trận\nAttention trung gian", ha='center', va='center', fontsize=8, weight='bold')
    
    ax1.add_patch(patches.FancyBboxPatch((1, 1.5), 4, 1, boxstyle="round,pad=0.1", facecolor='#E8F5E9', edgecolor='#43A047', linewidth=1.2))
    ax1.text(3, 2, "Hidden States đầu ra", ha='center', va='center', fontsize=9, weight='bold')
    
    # Crossed out attention weights represent lack of materialization
    ax1.add_patch(patches.Rectangle((6, 4.5), 3, 2, facecolor='#ECEFF1', edgecolor='#B0BEC5', linewidth=1, ls='--'))
    ax1.text(7.5, 5.5, "Ma trận Attention\n(N x N)\n(Bị bỏ qua/Không lưu)", ha='center', va='center', fontsize=8, color='#90A4AE', weight='bold')
    ax1.plot([6, 9], [4.5, 6.5], color='#D62728', lw=2)
    ax1.plot([6, 9], [6.5, 4.5], color='#D62728', lw=2)
    
    # Arrows Panel 1
    ax1.annotate('', xy=(3, 6.7), xytext=(3, 7.9), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    ax1.annotate('', xy=(3, 2.6), xytext=(3, 4.3), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    
    # Panel 2: Eager Attention
    ax2.set_title("Eager Attention (Tường minh, hỗ trợ Debug)", fontsize=11, weight='bold', pad=10)
    ax2.add_patch(patches.FancyBboxPatch((1, 8), 4, 1, boxstyle="round,pad=0.1", facecolor='#ECEFF1', edgecolor='#455A64', linewidth=1.2))
    ax2.text(3, 8.5, "Đầu vào Q, K, V", ha='center', va='center', fontsize=9, weight='bold')
    
    ax2.add_patch(patches.FancyBboxPatch((1, 4.5), 4, 2, boxstyle="round,pad=0.2", facecolor='#E1BEE7', edgecolor='#8E24AA', linewidth=1.5))
    ax2.text(3, 5.5, "Phép tính Eager\nQK^T -> Softmax -> * V\n(Từng bước tuần tự,\ntốn bộ nhớ hơn)", ha='center', va='center', fontsize=8, weight='bold')
    
    ax2.add_patch(patches.FancyBboxPatch((1, 1.5), 4, 1, boxstyle="round,pad=0.1", facecolor='#E8F5E9', edgecolor='#43A047', linewidth=1.2))
    ax2.text(3, 2, "Hidden States đầu ra", ha='center', va='center', fontsize=9, weight='bold')
    
    # Attention matrix is materialized
    ax2.add_patch(patches.Rectangle((6, 4.5), 3, 2, facecolor='#E8F5E9', edgecolor='#43A047', linewidth=1.5))
    # Draw a mock attention map grid
    for i in range(1, 4):
        ax2.plot([6, 9], [4.5 + i*0.5, 4.5 + i*0.5], color='#A5D6A7', lw=0.5)
        ax2.plot([6 + i*0.75, 6 + i*0.75], [4.5, 6.5], color='#A5D6A7', lw=0.5)
    ax2.text(7.5, 5.5, "Lưu trữ ma trận\nAttention (N x N)\nTrích xuất được\nAlignment!", ha='center', va='center', fontsize=8, color='#1B5E20', weight='bold')
    
    # Arrows Panel 2
    ax2.annotate('', xy=(3, 6.7), xytext=(3, 7.9), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    ax2.annotate('', xy=(3, 2.6), xytext=(3, 4.3), arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    ax2.annotate('', xy=(5.9, 5.5), xytext=(5.1, 5.5), arrowprops=dict(arrowstyle="->", color='#8E24AA', lw=1.5, ls='--'))
    
    plt.tight_layout()
    plt.savefig("figures/attention_sdpa_eager.png", bbox_inches='tight')
    plt.savefig("figures/attention_sdpa_eager.pdf", bbox_inches='tight')
    plt.close()
    print("Generated figures/attention_sdpa_eager.png and .pdf")

# ==========================================
# 5. PIPELINE FLOWCHART DIAGRAM (Figure 5)
# ==========================================
def draw_pipeline_flowchart():
    fig, ax = plt.subplots(figsize=(8.5, 6.5), dpi=300)
    ax.axis('off')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    
    # Define steps
    steps = [
        ("Thu thập & Cắt âm thanh từ YouTube", "Dùng yt_dlp, Faster-Whisper, WhisperX diarization để cắt WAV mono 16kHz", 8.2),
        ("Lọc & Làm sạch bộ dữ liệu", "Loại bỏ câu rỗng/nhiễu/quá ngắn -> Còn lại 1553 mẫu sạch (1476 Train / 77 Val)", 6.8),
        ("Chuẩn bị dữ liệu huấn luyện", "Chuyển văn bản sang Phonemes bằng G2P; encode âm thanh sang Speech Codecs", 5.4),
        ("Huấn luyện LoRA (VieNeu-0.3B)", "Đặt adapter LoRA (r=16) vào attention; train bằng CE Loss (T4 GPU, AdamW 8-bit)", 4.0),
        ("Sinh giọng nói (Inference)", "Kết hợp LoRA adapter + text mới + prompt giọng mồi -> tuần tự tạo ra audio mới", 2.6),
        ("Đánh giá tự động", "Chấm WER bằng Whisper-small và Speaker Similarity bằng ECAPA-TDNN", 1.2)
    ]
    
    for i, (title, desc, y) in enumerate(steps):
        # Draw step index box
        ax.add_patch(patches.FancyBboxPatch((0.5, y - 0.5), 0.7, 0.9, facecolor='#1F77B4', edgecolor='#1F77B4', boxstyle="round,pad=0.05"))
        ax.text(0.85, y - 0.05, str(i+1), color='white', ha='center', va='center', fontsize=12, weight='bold')
        
        # Draw text description box
        ax.add_patch(patches.FancyBboxPatch((1.5, y - 0.5), 7.8, 0.9, boxstyle="round,pad=0.05", facecolor='#F5F5F5', edgecolor='#CCCCCC', linewidth=1))
        ax.text(1.7, y + 0.15, title, ha='left', va='center', fontsize=10, weight='bold', color='#1F77B4')
        ax.text(1.7, y - 0.2, desc, ha='left', va='center', fontsize=8, color='#555555')
        
        # Draw connecting arrows between steps
        if i < len(steps) - 1:
            ax.annotate('', xy=(5, y - 0.53), xytext=(5, y - 0.97), arrowprops=dict(arrowstyle="<-", color='#888888', lw=1.5))
            
    ax.text(5, 9.7, "Pipeline huấn luyện & đánh giá Voice Cloning bằng LoRA", fontsize=13, weight='bold', ha='center')
    
    plt.tight_layout()
    plt.savefig("figures/tts_pipeline_flowchart.png", bbox_inches='tight')
    plt.savefig("figures/tts_pipeline_flowchart.pdf", bbox_inches='tight')
    plt.close()
    print("Generated figures/tts_pipeline_flowchart.png and .pdf")

if __name__ == "__main__":
    draw_data_split()
    draw_loss_curve()
    draw_model_comparison()
    draw_tts_architecture()
    draw_lora_architecture()
    draw_attention_comparison()
    draw_pipeline_flowchart()
    print("All 7 figures generated successfully!")
