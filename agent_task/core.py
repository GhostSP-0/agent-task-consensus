"""
agent_task v3 — Active Terminal Agents (with Background Process Management)
"""

import os
import time
import json
import uuid
import logging
import subprocess
import threading
from typing import Optional, Dict
import openai

from .prompts import BASE_SYSTEM, SYNTHESIS_SYSTEM, get_synthesis_prompt

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("AGENT_TASK_BASE_URL", "http://127.0.0.1:20128/v1")
API_KEY = os.getenv("AGENT_TASK_API_KEY", os.getenv("OPENAI_API_KEY", "sk-no-key"))

DEFAULT_MODEL1 = os.getenv("AGENT_TASK_MODEL1", "ag/gemini-3-flash-agent")
DEFAULT_MODEL2 = os.getenv("AGENT_TASK_MODEL2", "ag/claude-opus-4-6-thinking")
DEFAULT_MODEL3 = os.getenv("AGENT_TASK_MODEL3", "ag/claude-sonnet-4-6")

# Global dict to store background processes and their logs
BG_PROCESSES: Dict[str, dict] = {}

# --- Tools Definitions ---

TERMINAL_TOOL = {
    "type": "function",
    "function": {
        "name": "run_terminal",
        "description": "Jalankan shell command yang singkat dan pasti selesai (misal: ls, cat, echo).",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Bash command untuk dijalankan."}
            },
            "required": ["command"]
        }
    }
}

BACKGROUND_TOOL = {
    "type": "function",
    "function": {
        "name": "run_background",
        "description": "Jalankan command yang tidak akan berhenti (seperti server, ngrok, localtunnel). Mengembalikan process_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Bash command untuk dijalankan di background."}
            },
            "required": ["command"]
        }
    }
}

READ_LOG_TOOL = {
    "type": "function",
    "function": {
        "name": "read_background_log",
        "description": "Baca output log dari command background yang sedang berjalan.",
        "parameters": {
            "type": "object",
            "properties": {
                "process_id": {"type": "string", "description": "ID proses dari run_background."}
            },
            "required": ["process_id"]
        }
    }
}

ALL_TOOLS = [TERMINAL_TOOL, BACKGROUND_TOOL, READ_LOG_TOOL]

# --- Tool Handlers ---

def execute_command(command: str) -> str:
    """Run short shell command."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        output = result.stdout + result.stderr
        return output.strip() if output else "Command selesai tanpa output."
    except subprocess.TimeoutExpired:
        return "[Error: Command timeout (15s). Jika ini server/tunnel, gunakan run_background!]"
    except Exception as e:
        return f"[Error: {str(e)}]"

def run_bg_command(command: str) -> str:
    """Run long-lived shell command in background."""
    proc_id = str(uuid.uuid4())[:8]
    log_file = f"/tmp/bg_{proc_id}.log"
    
    # Run command completely detached, redirecting all output to log_file
    full_cmd = f"nohup {command} > {log_file} 2>&1 &"
    subprocess.run(full_cmd, shell=True)
    
    BG_PROCESSES[proc_id] = {"log_file": log_file, "command": command}
    return f"Proses {proc_id} mulai berjalan di background. Gunakan read_background_log dengan process_id '{proc_id}' setelah beberapa detik untuk melihat outputnya."

def read_bg_log(process_id: str) -> str:
    """Read log file of a background process."""
    if process_id not in BG_PROCESSES:
        return f"[Error: process_id '{process_id}' tidak ditemukan.]"
    
    log_file = BG_PROCESSES[process_id]["log_file"]
    try:
        with open(log_file, "r") as f:
            lines = f.readlines()
            
        if not lines:
            return "[Log masih kosong. Mungkin proses belum mencetak output.]"
        
        # Return last 30 lines
        out = "".join(lines[-30:])
        return out.strip()
    except Exception as e:
        return f"[Error membaca log: {str(e)}]"

# --- Agent Query ---

def _query_basic(model_id: str, system_prompt: str, user_prompt: str) -> str:
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

def _query_with_tools(model_id: str, system_prompt: str, user_prompt: str) -> str:
    client = openai.OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Allow agent up to 12 tool interaction loops
    for step in range(12):
        try:
            # Give API a tiny break to prevent 429 inside the loop
            if step > 0:
                time.sleep(2)
                
            resp = client.chat.completions.create(
                model=model_id,
                messages=messages,
                tools=ALL_TOOLS,
                tool_choice="auto",
                temperature=0.5
            )
            message = resp.choices[0].message
            messages.append(message)
            
            if not message.tool_calls:
                return message.content or ""
            
            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                cmd_result = ""
                if fn_name == "run_terminal":
                    cmd_result = execute_command(args.get("command", ""))
                elif fn_name == "run_background":
                    cmd_result = run_bg_command(args.get("command", ""))
                    # Wait 2 seconds so the service has time to write logs before the agent inevitably calls read_log
                    time.sleep(2) 
                elif fn_name == "read_background_log":
                    cmd_result = read_bg_log(args.get("process_id", ""))
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": cmd_result
                })
        except Exception as e:
            return f"[FATAL ERROR in agent loop: {e}]\nFinal accumulated context: {message.content if 'message' in locals() else 'None'}"
    
    return "Agent dihentikan karena mencapai batas maksimal penggunaan tools (12 langkah)."

# --- Main Logic ---

def agent_task(
    task: str,
    model1: Optional[str] = None,
    model2: Optional[str] = None,
    model3: Optional[str] = None,
    output_file: Optional[str] = None,
) -> str:
    t0 = time.time()
    m1 = model1 or DEFAULT_MODEL1
    m2 = model2 or DEFAULT_MODEL2
    m3 = model3 or DEFAULT_MODEL3
    
    # Cleanup old logs
    subprocess.run("rm -f /tmp/bg_*.log", shell=True)
    
    logger.info("Mulai Agent 1 (Drafting)...")
    draft1 = _query_basic(m1, BASE_SYSTEM, task)
    
    logger.info("Mulai Agent 2 (Drafting)...")
    time.sleep(5)
    draft2 = _query_basic(m2, BASE_SYSTEM, task)
    
    logger.info("Mulai Agent 3 (Synthesis + Tools)...")
    time.sleep(5)
    compilation = f"--- DRAF DARI {m1} ---\n{draft1}\n\n--- DRAF DARI {m2} ---\n{draft2}"
    synthesis_prompt = get_synthesis_prompt(task, compilation)
    
    final_result = _query_with_tools(m3, SYNTHESIS_SYSTEM, synthesis_prompt)
    
    elapsed = time.time() - t0
    
    output = (
        f"### 🤖 ACTIVE CONSENSUS AGENT (V4)\n\n"
        f"**Drafters:** {m1}, {m2}\n"
        f"**Verifikator (Terminal Access):** {m3}\n"
        f"**Waktu Eksekusi:** {elapsed:.1f}s\n\n"
        f"---\n\n"
        f"#### HASIL FINAL (Terverifikasi):\n"
        f"{final_result}"
    )
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
            
    return output
