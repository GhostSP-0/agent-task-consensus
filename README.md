# Agent Task Consensus (V3 - Active Agents)

Agent Task Consensus adalah sistem multi-agent di mana tiga agen AI berkolaborasi untuk memecahkan masalah. Di versi V3 ini, sistem telah dirombak total menjadi **Active Agents** yang berjalan di background, sangat hemat token, kebal terhadap rate-limit, dan agen penengah memiliki akses terminal murni.

## 🚀 Fitur Utama (V3)
- **Background Execution:** Berjalan di latar belakang tanpa memblokir chat utama.
- **Hemat Token (No Bloat):** Tidak mengirimkan system prompt raksasa berulang kali. Hanya mengirim instruksi yang sangat presisi ke masing-masing model (2000-an token per siklus).
- **Sequential Anti-Rate Limit:** Agen berjalan bergantian dengan jeda, mencegah error `HTTP 429 Quota Reached` di API provider.
- **Active Verifier (Terminal Access):** Agen sintesis (Agen ke-3) *tidak sekadar merangkum*. Dia memiliki akses `run_terminal` untuk secara nyata membuat file, menjalankan script, dan membuktikan kode/draf sebelum memberikan kesimpulan akhir.

## 🛠️ Arsitektur
1. **Agent 1 (Drafter):** Memberikan ide/solusi mentah awal (Default: Gemini Flash)
2. **Agent 2 (Drafter):** Memberikan ide/solusi alternatif (Default: Claude Opus)
3. **Agent 3 (Verifikator & Sintesis):** Menganalisis draf 1 dan 2, menjalankan script uji coba di terminal, mengamati error, dan mensintesis solusi yang telah **terbukti berjalan nyata** (Default: Claude Sonnet)

## 📦 Instalasi

1. Clone repositori ini:
   ```bash
   git clone https://github.com/GhostSP-0/agent-task-consensus.git
   cd agent-task-consensus
   ```

2. Buat file wrapper `agent-task` (Optional tapi direkomendasikan):
   ```bash
   cat << 'EOF' > /usr/local/bin/agent-task
   #!/bin/bash
   if [ -z "$1" ]; then echo "Usage: agent-task \"tugas yang mau dikerjakan\""; exit 1; fi
   
   # Konfigurasi API Anda
   export AGENT_TASK_API_KEY="sk-API-KEY-ANDA"
   export AGENT_TASK_BASE_URL="http://URL-BASE-ANDA:PORT/v1"
   export OPENAI_API_KEY="$AGENT_TASK_API_KEY"
   
   python3 /usr/root/agent-task-consensus/agent_task_runner.py "$1" --output "/tmp/agent_task_$(date +%s).md"
   EOF
   chmod +x /usr/local/bin/agent-task
   ```

## 🎮 Cara Penggunaan

### 1. Via Terminal Langsung
```bash
python3 agent_task_runner.py "Buatkan script python untuk deret fibonacci ke-10, jalankan dan berikan hasilnya." --output /tmp/hasil.md
```

### 2. Via Integrasi Hermes Agent (Chat)
Jika Anda menggunakan Hermes, Anda cukup memerintahkan Hermes di chat:
> **"agent-task buatkan script backup server"**

Hermes secara otomatis akan melemparkan tugas ke background, membiarkan 3 agen bekerja & memverifikasi solusi, lalu mencetak hasilnya kepada Anda saat selesai.

---
*Dikembangkan oleh GhostSP-0 & Antigravity*