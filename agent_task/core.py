import os
import logging
import threading
from typing import Dict, List, Any, Optional
import openai

from .prompts import (
    BASE_SYSTEM,
    CRITIQUE_SYSTEM_TEMPLATE,
    get_critique_prompt,
    SYNTHESIS_SYSTEM,
    get_synthesis_prompt
)

logger = logging.getLogger(__name__)

# Base config (defaults to local environment but can be overridden via env vars)
API_BASE_URL = os.getenv("AGENT_TASK_BASE_URL", "http://127.0.0.1:20128/v1")
API_KEY = os.getenv("AGENT_TASK_API_KEY", "«redacted:sk-…»")

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
    def worker_phase1(agent_key: str, model_name: str):
        results[agent_key] = run_agent_query(model_name, BASE_SYSTEM, task)

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

        critique_prompt = get_critique_prompt(task, other_drafts)
        critique_system = CRITIQUE_SYSTEM_TEMPLATE.format(critic_model=critic_model)
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
    synthesis_model = m1
    
    compilation = "=== DRAF AWAL AGEN ===\n"
    for k, v in results.items():
        compilation += f"\n--- {k.upper()} DRAFT (Model: {active_models[k]}) ---\n{v}\n"
        
    compilation += "\n\n=== MASUKAN KRITIK & REKOMENDASI SALING SILANG ===\n"
    for k, v in critiques.items():
        compilation += f"\n--- KRITIK DARI {k.upper()} (Model: {active_models[k]}) ---\n{v}\n"

    synthesis_prompt = get_synthesis_prompt(task, compilation)
    final_consensus = run_agent_query(synthesis_model, SYNTHESIS_SYSTEM, synthesis_prompt)

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
