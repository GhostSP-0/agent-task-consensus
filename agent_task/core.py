"""
agent_task (Meja Bundar / Parallel Consensus Tanpa Akses Terminal dari Agen)
"""

import os
import time
import logging
from typing import Optional, Dict
import openai
from concurrent.futures import ThreadPoolExecutor, as_completed

from .prompts import BASE_SYSTEM, SYNTHESIS_SYSTEM, get_synthesis_prompt

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("AGENT_TASK_BASE_URL", "http://127.0.0.1:20128/v1")
API_KEY = os.getenv("AGENT_TASK_API_KEY", os.getenv("OPENAI_API_KEY", "sk-no-key"))

DEFAULT_MODEL1 = os.getenv("AGENT_TASK_MODEL1", "ag/gemini-3-flash-agent")
DEFAULT_MODEL2 = os.getenv("AGENT_TASK_MODEL2", "ag/claude-opus-4-6-thinking")
DEFAULT_MODEL3 = os.getenv("AGENT_TASK_MODEL3", "ag/claude-sonnet-4-6")


def _query_basic(model_id: str, system_prompt: str, user_prompt: str) -> str:
    """Kirim request ke satu model tanpa tools apapun."""
    client = openai.OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    try:
        resp = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"[ERROR {model_id}: {e}]"


def agent_task(
    task: str,
    model1: Optional[str] = None,
    model2: Optional[str] = None,
    model3: Optional[str] = None,
    output_file: Optional[str] = None,
) -> str:
    t0 = time.time()
    
    # Model Setup
    m1 = model1 or DEFAULT_MODEL1
    m2 = model2 or DEFAULT_MODEL2
    m3 = model3 or DEFAULT_MODEL3
    
    models = {
        "Agen 1": m1,
        "Agen 2": m2,
        "Agen 3": m3
    }
    
    logger.info("Tahap 1: Melempar tugas ke ketiga agen secara bersamaan...")
    
    drafts = {}
    # Kita jalankan secara berurutan tapi cepat, biar API gak kena rate limit 429
    for nama_agen, id_model in models.items():
        logger.info(f"{nama_agen} ({id_model}) sedang memikirkan ide...")
        drafts[nama_agen] = _query_basic(id_model, BASE_SYSTEM, task)
        time.sleep(3) # Jeda aman anti limit
        
    logger.info("Tahap 2: Menggabungkan hasil mereka (Sintesis)...")
    
    compilation = ""
    for nama_agen, isi_draft in drafts.items():
        compilation += f"\n--- IDE DARI {nama_agen} ({models[nama_agen]}) ---\n{isi_draft}\n"
        
    synthesis_prompt = get_synthesis_prompt(task, compilation)
    
    # Gua (Gemini Pro Agent / Atau siapapun yg dipake buat m3) bertindak sebagai Ketua Konsensus yg gabungin
    final_result = _query_basic(m3, SYNTHESIS_SYSTEM, synthesis_prompt)
    
    elapsed = time.time() - t0
    
    output = (
        f"### 🤝 KONSENSUS MEJA BUNDAR (AGEN-TASK)\n\n"
        f"**Tugas:** {task}\n"
        f"**Agen:** {m1} | {m2} | {m3}\n"
        f"**Waktu:** {elapsed:.1f}s\n\n"
        f"---\n\n"
        f"#### HASIL GABUNGAN FINAL:\n"
        f"{final_result}\n\n"
        f"---\n"
        f"<details><summary>Klik untuk melihat ide mentah dari masing-masing Agen</summary>\n{compilation}\n</details>"
    )
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
            
    return output
