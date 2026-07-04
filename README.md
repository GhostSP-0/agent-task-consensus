# 🤖 Agent-Task: Multi-Agent Consensus System

`agent-task` adalah sistem kolaborasi Multi-Agent (MoA - Mixture of Agents) berbasis Python yang dirancang untuk menghasilkan jawaban dengan kualitas, akurasi, dan kedalaman terbaik lewat metode **Paralelisasi, Saling Kritik (Cross-Critique), dan Konsensus Akhir**.

Sistem ini didesain khusus agar dapat dijalankan secara mandiri via CLI, skrip Python, maupun diintegrasikan langsung sebagai kustom tool di berbagai AI Agent Harness seperti **Hermes Agent, Claude Code, Cursor, atau VS Code**.

---

## 🌟 Kelebihan `agent-task`

1.  **Pendekatan Multi-Model (MoA):** Memanfaatkan keunggulan dari 3 model AI top-tier sekaligus dalam satu waktu:
    *   **Agent 1 (Claude Opus Thinking):** Ahli dalam penalaran mendalam (*deep reasoning*).
    *   **Agent 2 (Gemini Flash):** Cepat, efisien, dan memiliki basis data pengetahuan luas.
    *   **Agent 3 (Claude Sonnet 4.6):** Presisi, handal dalam pemrograman, dan penulisan terstruktur.
2.  **Saling Kritik & Evaluasi (Cross-Critique):** Sebelum memberikan jawaban akhir ke user, ketiga agen ini saling membaca draf satu sama lain, mencari kekurangan, dan saling mengoreksi secara otomatis.
3.  **Konsensus Optimal:** Hasil draf awal beserta seluruh masukan kritik diramu ulang oleh model terbaik (`Claude Opus Thinking`) untuk melahirkan satu jawaban akhir yang matang dan minim kesalahan (halusinasi).
4.  **Mudah Diintegrasikan:** Berupa modul Python portabel dengan dukungan format tool standar (`JSON Schema`), membuatnya sangat mudah dipasang sebagai MCP Server atau custom tool di platform AI mana saja.

---

## 🚀 Cara Kerja (Step-by-Step)

```
[ User Task ] 
      │
      ├──> (Paralel) ──> Agent 1 (Opus) ─────────> Draf 1 ──┐
      ├──> (Paralel) ──> Agent 2 (Gemini) ───────> Draf 2 ──┼──> [ Saling Kritik ]
      └──> (Paralel) ──> Agent 3 (Sonnet) ───────> Draf 3 ──┘           │
                                                                        ▼
[ Jawaban Konsensus Akhir ] <─── (Sintesis) <─── Agent 1 (Opus) <───────┘
```

---

## 🛠️ Panduan Penggunaan

### 1. Prasyarat (Requirements)
Pastikan Python 3.9+ sudah terpasang beserta library OpenAI:
```bash
pip install openai
```

Secara default, skrip ini mengarah ke API endpoint lokal port `20128`. Jika Anda ingin menghubungkannya ke penyedia API luar (seperti OpenRouter), Anda dapat mengekspor environment variables berikut di terminal:
```bash
export AGENT_TASK_BASE_URL="https://openrouter.ai/api/v1"
export AGENT_TASK_API_KEY="your-openrouter-api-key"
```

### 2. Dijalankan Langsung via CLI (Terminal)
Anda bisa mengeksekusi skrip ini langsung dari terminal untuk mendapatkan jawaban instan:
```bash
python3 agent_task.py "Tuliskan 3 resep makanan pembuka yang mudah dibuat"
```

### 3. Diintegrasikan sebagai Custom Tool di Claude Code
Agar Claude Code (atau agen CLI lainnya) bisa memanggil fungsi `agent-task` ini secara otomatis, letakkan file `agent_task.py` di direktori proyek Anda dan definisikan skrip pemanggilnya di file konfigurasi tools milik Claude Code (atau `CLAUDE.md` / `AGENTS.md`):

#### Contoh definisi tool di `AGENTS.md` / `CLAUDE.md`:
```markdown
## Custom Tools
- **agent_task**: Gunakan tool ini untuk menyelesaikan tugas analisis, pemecahan masalah, atau penulisan yang rumit menggunakan kolaborasi multi-agent.
  - Perintah: `python3 /absolute/path/to/agent_task.py "<task_description>"`
```

### 4. Diimpor ke Skrip Python Lain
Anda juga bisa memanggilnya langsung di dalam kode Python Anda:
```python
from agent_task import agent_task

hasil = agent_task("Jelaskan perbedaan SQL dan NoSQL.")
print(hasil)
```
