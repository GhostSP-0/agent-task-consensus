# 🤖 Agent-Task: Multi-Agent Consensus System

`agent-task` adalah sistem kolaborasi Multi-Agent (MoA - Mixture of Agents) berbasis Python yang dirancang untuk menghasilkan jawaban dengan kualitas, akurasi, dan kedalaman terbaik lewat metode **Paralelisasi, Saling Kritik (Cross-Critique), dan Konsensus Akhir**.

Sistem ini didesain khusus agar dapat dijalankan secara mandiri via CLI, skrip Python, maupun diintegrasikan langsung sebagai kustom tool di berbagai AI Agent Harness seperti **Hermes Agent, Claude Code, Cursor, atau VS Code**.

---

## 🌟 Kelebihan `agent-task`

1.  **Dinamis & Fleksibel (Bebas Pilih Model):** Tidak terpaku pada 3 model bawaan. Anda dapat menentukan 3 model kustom yang berbeda secara dinamis sesuai kebutuhan saat memanggil tool atau melalui environment variables.
2.  **Cross-Critique Berkelanjutan:** Sebelum menyusun jawaban konsensus, ketiga agen saling mengevaluasi draf satu sama lain untuk mencari kesalahan logika, celah informasi, atau klaim yang meragukan.
3.  **Konsensus Berkualitas Tinggi (Sintesis Optimal):** Hasil draf awal dan kritik saling silang diramu oleh Chief Editor/Synthesizer menjadi satu output konsensus yang solid, komprehensif, dan sangat meyakinkan.
4.  **Desain Portabel:** Berupa satu modul Python mandiri yang dapat dicolokkan ke editor coding/agent framework favorit Anda sebagai custom tool.

---

## 🚀 Alur Kerja (Workflow)

```
[ User Task ] 
      │
      ├──> (Paralel) ──> Agent 1 (Model A) ──────> Draf 1 ──┐
      ├──> (Paralel) ──> Agent 2 (Model B) ──────> Draf 2 ──┼──> [ Saling Kritik ]
      └──> (Paralel) ──> Agent 3 (Model C) ──────> Draf 3 ──┘           │
                                                                        ▼
[ Jawaban Konsensus Akhir ] <─── (Sintesis) <─── Agent 1 (Model A) <────┘
```

---

## 🛠️ Panduan Penggunaan & Integrasi

### 1. Instalasi Dependensi
Pastikan Python 3.9+ sudah terpasang beserta library resmi OpenAI SDK:
```bash
pip install openai
```

### 2. Mengatur Endpoint API (Opsional)
Jika Anda menggunakan model di luar backend lokal (misalnya menggunakan OpenRouter atau endpoint OpenAI resmi), silakan set environment variables berikut di terminal:
```bash
export AGENT_TASK_BASE_URL="https://openrouter.ai/api/v1"
export AGENT_TASK_API_KEY="your-openrouter-api-key"
```

### 3. Dijalankan Langsung via CLI (Terminal)
Eksekusi langsung melalui command terminal. Secara default, sistem akan menggunakan model bawaan (Opus Thinking, Gemini Flash, dan Sonnet 4.6).
```bash
python3 agent_task.py "Jelaskan cara kerja HTTPS secara detail"
```

Untuk mengganti model default secara permanen tanpa mengedit kode, ekspor env berikut sebelum menjalankan:
```bash
export AGENT_TASK_MODEL1="ag/claude-opus-4-6-thinking"
export AGENT_TASK_MODEL2="ag/gemini-3-flash-agent"
export AGENT_TASK_MODEL3="ag/claude-sonnet-4-6"
```

### 4. Diintegrasikan sebagai Custom Tool di Claude Code
Agar Claude Code (atau agen CLI lainnya) dapat memanggil `agent-task` secara otomatis, daftarkan tool ini dalam konfigurasi proyek Anda (`CLAUDE.md` atau `AGENTS.md`):

#### Contoh definisi di `CLAUDE.md` / `AGENTS.md`:
```markdown
## Custom Tools
- **agent_task**: Run complex tasks through a 3-agent consensus pool.
  - Usage: `python3 /absolute/path/to/agent_task.py "<task_description>"`
```

### 5. Digunakan dalam Kode Python Lain
Anda dapat mengimpor fungsinya dan menentukan model kustom secara dinamis di dalam kode Python:
```python
from agent_task import agent_task

# Memanggil dengan model kustom (Contoh: menggunakan model GLM)
hasil = agent_task(
    task="Analisis kelemahan algoritma MD5",
    model1="zai/glm-5",
    model2="ag/gemini-3.5-flash",
    model3="ag/claude-sonnet-4-6"
)

print(hasil)
```
