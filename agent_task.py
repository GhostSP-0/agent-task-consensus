import os
import json
import logging
import threading
from typing import Dict, List, Any
import openai

logger = logging.getLogger(__name__)

# Base config (defaults to local environment but can be overridden via env vars)
API_BASE_URL = os.getenv("AGENT_TASK_BASE_URL", "http://127.0.0.1:20128/v1")
API_KEY = os.getenv("AGENT_TASK_API_KEY", "sk-44e8bc92d1c676d1e434e7f827ee784841f4")

# The 3 target models
MODELS = {
    "agent1": "ag/claude-opus-4-6-thinking",
    "agent2": "ag/gemini-3-flash-agent",
    "agent3": "ag/claude-sonnet-4-6"
}

def get_openai_client():
    return openai.OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY
    )

def run_agent_query(model_id: str, system_prompt: str, user_prompt: str) -> str:
    """Run a single LLM request on a specific model."""
    client = get_openai_client()
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"Error querying model {model_id}: {e}")
        return f"Error: Gagal mendapatkan respon dari model {model_id}. Detail: {str(e)}"

def agent_task(task: str) -> str:
    """
    Core function for the agent_task tool.
    1. Query Agent 1, 2, and 3 in parallel with the user's task.
    2. Collect their initial answers.
    3. Run a mutual critique round.
    4. Compile the final optimized consensus output.
    """
    results = {}
    threads = []

    # -------------------------------------------------------------
    # PHASE 1: Gather Initial Answers (Parallel)
    # -------------------------------------------------------------
    base_system = (
        "Kamu adalah AI Agent ahli. Berikan jawaban terbaik, paling akurat, "
        "dan detail untuk tugas berikut. Jawab dalam bahasa Indonesia."
    )

    def worker_phase1(agent_key: str, model_name: str):
        results[agent_key] = run_agent_query(model_name, base_system, task)

    for key, model in MODELS.items():
        t = threading.Thread(target=worker_phase1, args=(key, model))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # -------------------------------------------------------------
    # PHASE 2: Cross-Critique (Parallel)
    # -------------------------------------------------------------
    critiques = {}
    critique_threads = []

    def worker_critique(critic_key: str, critic_model: str):
        other_drafts = ""
        for k, v in results.items():
            if k != critic_key:
                other_drafts += f"=== DRAFT DARI {k.upper()} ===\n{v}\n\n"

        critique_prompt = (
            f"Tugas Awal: {task}\n\n"
            f"Berikut adalah draf jawaban dari agen-agen lain:\n\n{other_drafts}"
            f"Tugas kamu sekarang adalah menganalisis draf mereka secara kritis. "
            f"Tunjukkan bagian mana yang kurang tepat, bagian mana yang perlu ditambahkan, "
            f"dan berikan rekomendasi perbaikan yang konkret. Jawab dengan ringkas dan objektif dalam bahasa Indonesia."
        )
        
        critique_system = f"Kamu adalah analis kritis untuk model {MODELS[critic_key]}."
        critiques[critic_key] = run_agent_query(critic_model, critique_system, critique_prompt)

    for key, model in MODELS.items():
        t = threading.Thread(target=worker_critique, args=(key, model))
        critique_threads.append(t)
        t.start()

    for t in critique_threads:
        t.join()

    # -------------------------------------------------------------
    # PHASE 3: Synthesis & Consensus Generation
    # -------------------------------------------------------------
    synthesis_model = MODELS["agent1"]
    
    compilation = "=== DRAF AWAL ===\n"
    for k, v in results.items():
        compilation += f"\n--- {k.upper()} DRAFT ---\n{v}\n"
        
    compilation += "\n\n=== HASIL KRITIK & EVALUASI SALING SILANG ===\n"
    for k, v in critiques.items():
        compilation += f"\n--- EVALUASI DARI {k.upper()} ---\n{v}\n"

    synthesis_prompt = (
        f"Tugas Awal: {task}\n\n"
        f"Kamu diberikan kumpulan draf awal dan kritik saling silang dari 3 agen berikut:\n\n"
        f"{compilation}\n\n"
        f"Tugas Akhir Kamu:\n"
        f"Gabungkan, perbaiki, dan optimalkan semua hasil kerja di atas menjadi satu jawaban akhir yang sempurna, "
        f"padat, akurat, dan memiliki kualitas terbaik sesuai dengan masukan kritik dari para agen. "
        f"Tulis jawaban akhir secara terstruktur dalam bahasa Indonesia yang baik."
    )

    synthesis_system = (
        "Kamu adalah Master Aggregator. Tugasmu menyatukan berbagai draf "
        "dan masukan kritik menjadi satu kesimpulan konsensus akhir berkualitas tinggi."
    )

    final_consensus = run_agent_query(synthesis_model, synthesis_system, synthesis_prompt)

    formatted_output = (
        f"### 🤖 PROSES MULTI-AGENT COLLABORATION (`agent_task`)\n\n"
        f"#### 1️⃣ Draf Awal:\n"
        f"*   **Agent 1 (Opus Thinking):** Selesai\n"
        f"*   **Agent 2 (Gemini Flash):** Selesai\n"
        f"*   **Agent 3 (Sonnet 4.6):** Selesai\n\n"
        f"#### 2️⃣ Hasil Saling Kritik:\n"
        f"*   *Agent 1 mengoreksi draf Agent 2 & 3.*\n"
        f"*   *Agent 2 memberikan masukan untuk draf Agent 1 & 3.*\n"
        f"*   *Agent 3 mengevaluasi draf Agent 1 & 2.*\n\n"
        f"#### 3️⃣ Konsensus Jawaban Akhir (Optimal):\n\n"
        f"{final_consensus}"
    )

    return formatted_output

if __name__ == "__main__":
    import sys
    test_task = sys.argv[1] if len(sys.argv) > 1 else "Jelaskan apa itu database PostgreSQL secara singkat."
    print(agent_task(test_task))
