import os
import json
import logging
import threading
from typing import Dict, List, Any, Optional
import openai

logger = logging.getLogger(__name__)

# Base config (defaults to local environment but can be overridden via env vars)
API_BASE_URL = os.getenv("AGENT_TASK_BASE_URL", "http://127.0.0.1:20128/v1")
API_KEY = os.getenv("AGENT_TASK_API_KEY", "sk-44e8bc92d1c676d1e434e7f827ee784841f4")

# Fallback default models if user doesn't specify any
DEFAULT_MODEL1 = os.getenv("AGENT_TASK_MODEL1", "ag/claude-opus-4-6-thinking")
DEFAULT_MODEL2 = os.getenv("AGENT_TASK_MODEL2", "ag/gemini-3-flash-agent")
DEFAULT_MODEL3 = os.getenv("AGENT_TASK_MODEL3", "ag/claude-sonnet-4-6")

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

def agent_task(
    task: str,
    model1: Optional[str] = None,
    model2: Optional[str] = None,
    model3: Optional[str] = None
) -> str:
    """
    Core function for the agent_task tool.
    1. Query Agent 1, 2, and 3 in parallel with the user's task.
    2. Collect their initial answers.
    3. Run a mutual critique round.
    4. Compile the final optimized consensus output.
    """
    m1 = model1 or DEFAULT_MODEL1
    m2 = model2 or DEFAULT_MODEL2
    m3 = model3 or DEFAULT_MODEL3

    active_models = {
        "agent1": m1,
        "agent2": m2,
        "agent3": m3
    }

    results = {}
    threads = []

    # -------------------------------------------------------------
    # PHASE 1: Gather Initial Answers (Parallel)
    # -------------------------------------------------------------
    base_system = (
        "Kamu adalah pakar domain tingkat dunia yang sangat cerdas, objektif, dan teliti. "
        "Tugasmu adalah memberikan analisis awal yang mendalam, komprehensif, "
        "dan sangat akurat untuk tugas berikut. Jawab dalam bahasa Indonesia dengan struktur yang baik."
    )

    def worker_phase1(agent_key: str, model_name: str):
        results[agent_key] = run_agent_query(model_name, base_system, task)

    for key, model in active_models.items():
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
                other_drafts += f"=== DRAFT DARI {k.upper()} (Model: {active_models[k]}) ===\n{v}\n\n"

        critique_prompt = (
            f"Tugas Awal yang harus diselesaikan: {task}\n\n"
            f"Berikut adalah draf jawaban dari agen-agen lain:\n\n{other_drafts}"
            f"Tugas kamu sekarang adalah menganalisis draf mereka secara kritis dan tajam. "
            f"Tunjukkan celah faktual, ketidakkonsistenan logika, hal-hal yang terlewatkan (omissions), "
            f"atau penjelasan yang kurang maksimal. Berikan rekomendasi spesifik dan langkah konkret "
            f"untuk memperbaiki dan menyempurnakan jawaban tersebut agar meyakinkan. "
            f"Jawab dengan lugas, objektif, dan profesional dalam bahasa Indonesia."
        )
        
        critique_system = f"Kamu adalah evaluator kritis utama untuk model {critic_model}."
        critiques[critic_key] = run_agent_query(critic_model, critique_system, critique_prompt)

    for key, model in active_models.items():
        t = threading.Thread(target=worker_critique, args=(key, model))
        critique_threads.append(t)
        t.start()

    for t in critique_threads:
        t.join()

    # -------------------------------------------------------------
    # PHASE 3: Synthesis & Consensus Generation
    # -------------------------------------------------------------
    # We use agent1 (or fall back to m1) for the final synthesis & consensus building.
    synthesis_model = m1
    
    compilation = "=== DRAF AWAL AGEN ===\n"
    for k, v in results.items():
        compilation += f"\n--- {k.upper()} DRAFT (Model: {active_models[k]}) ---\n{v}\n"
        
    compilation += "\n\n=== MASUKAN KRITIK & REKOMENDASI SALING SILANG ===\n"
    for k, v in critiques.items():
        compilation += f"\n--- KRITIK DARI {k.upper()} (Model: {active_models[k]}) ---\n{v}\n"

    synthesis_prompt = (
        f"Tugas Utama: {task}\n\n"
        f"Kamu diberikan draf awal beserta kritik & evaluasi dari 3 agen ahli berikut:\n\n"
        f"{compilation}\n\n"
        f"TUGAS AKHIR KAMU:\n"
        f"1. Gabungkan kelebihan dari ketiga draf tersebut.\n"
        f"2. Koreksi semua kesalahan atau bagian yang kurang tepat berdasarkan poin-poin kritik yang masuk.\n"
        f"3. Tambahkan penjelasan baru jika ada celah informasi yang ditemukan dalam proses kritik.\n"
        f"4. Hasilkan satu jawaban akhir konsensus yang sempurna, sangat komprehensif, logis, "
        f"terstruktur rapi, dan memiliki tingkat keandalan yang sangat tinggi (sangat meyakinkan).\n\n"
        f"Tulis jawaban akhir secara mendalam dan profesional dalam bahasa Indonesia."
    )

    synthesis_system = (
        "Kamu adalah Master Aggregator & Chief Editor. Tugasmu adalah mengintegrasikan draf "
        "dan masukan kritik secara objektif untuk menghasilkan output konsensus final dengan kualitas terbaik."
    )

    final_consensus = run_agent_query(synthesis_model, synthesis_system, synthesis_prompt)

    # Format output for the user
    formatted_output = (
        f"### 🤖 PROSES MULTI-AGENT COLLABORATION (`agent_task`)\n\n"
        f"#### 1️⃣ Konfigurasi Model:\n"
        f"*   **Agent 1:** `{m1}`\n"
        f"*   **Agent 2:** `{m2}`\n"
        f"*   **Agent 3:** `{m3}`\n\n"
        f"#### 2️⃣ Status Eksekusi:\n"
        f"*   **Fase 1 (Draf Paralel):** Selesai\n"
        f"*   **Fase 2 (Saling Kritik):** Selesai\n"
        f"*   **Fase 3 (Sintesis Konsensus):** Selesai\n\n"
        f"#### 3️⃣ Konsensus Jawaban Akhir (Optimal & Meyyakinkan):\n\n"
        f"{final_consensus}"
    )

    return formatted_output

if __name__ == "__main__":
    import sys
    test_task = sys.argv[1] if len(sys.argv) > 1 else "Jelaskan apa itu database PostgreSQL secara singkat."
    print(agent_task(test_task))
