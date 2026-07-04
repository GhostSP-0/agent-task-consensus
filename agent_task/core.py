"""
agent_task v3 — Active Terminal Agents (Sequential to bypass API Rate Limits)
"""

import os
import time
import json
import logging
import subprocess
from typing import Optional
import openai

from .prompts import BASE_SYSTEM, SYNTHESIS_SYSTEM, get_synthesis_prompt

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("AGENT_TASK_BASE_URL", "http://127.0.0.1:20128/v1")
API_KEY = os.getenv("AGENT_TASK_API_KEY", os.getenv("OPENAI_API_KEY", "sk-no-key"))

DEFAULT_MODEL1 = os.getenv("AGENT_TASK_MODEL1", "ag/gemini-3-flash-agent")
DEFAULT_MODEL2 = os.getenv("AGENT_TASK_MODEL2", "ag/claude-opus-4-6-thinking")
DEFAULT_MODEL3 = os.getenv("AGENT_TASK_MODEL3", "ag/claude-sonnet-4-6")

# Tools definition for the Synthesis Agent
TERMINAL_TOOL = {
    "type": "function",
    "function": {
        "name": "run_terminal",
        "description": "Execute a shell command in the Linux terminal.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to run (e.g. 'python3 script.py', 'ls -la', 'cat file.txt')"
                }
            },
            "required": ["command"]
        }
    }
}

def execute_command(command: str) -> str:
    """Run shell command and return stdout/stderr."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        return output.strip() if output else "Command executed successfully with no output."
    except subprocess.TimeoutExpired:
        return "[Error: Command timed out after 30 seconds]"
    except Exception as e:
        return f"[Error: {str(e)}]"

def _query_basic(model_id: str, system_prompt: str, user_prompt: str) -> str:
    """Basic text generation (no tools)."""
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
    """Agent loop with terminal access."""
    client = openai.OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Allow agent to run up to 5 steps of tools
    for step in range(5):
        try:
            resp = client.chat.completions.create(
                model=model_id,
                messages=messages,
                tools=[TERMINAL_TOOL],
                tool_choice="auto",
                temperature=0.5
            )
            message = resp.choices[0].message
            messages.append(message)
            
            if not message.tool_calls:
                # No more tool calls, agent is done
                return message.content or ""
            
            # Execute tool calls
            for tool_call in message.tool_calls:
                if tool_call.function.name == "run_terminal":
                    args = json.loads(tool_call.function.arguments)
                    cmd = args.get("command", "")
                    cmd_result = execute_command(cmd)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": cmd_result
                    })
        except Exception as e:
            return f"[FATAL ERROR in agent loop: {e}]\nFinal accumulated context: {message.content}"
    
    return "Agent stopped after reaching maximum steps (5)."

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
    
    # Sequential execution to prevent 429 Rate Limits
    logger.info("Mulai Agent 1 (Drafting)...")
    draft1 = _query_basic(m1, BASE_SYSTEM, task)
    
    logger.info("Mulai Agent 2 (Drafting)... tunggu 5 detik biar ga kena limit")
    time.sleep(5) # Delay 5 detik
    draft2 = _query_basic(m2, BASE_SYSTEM, task)
    
    logger.info("Mulai Agent 3 (Synthesis + Terminal Tools)... tunggu 5 detik lagi")
    time.sleep(5) # Delay 5 detik lagi
    compilation = f"--- DRAF DARI {m1} ---\n{draft1}\n\n--- DRAF DARI {m2} ---\n{draft2}"
    synthesis_prompt = get_synthesis_prompt(task, compilation)
    
    final_result = _query_with_tools(m3, SYNTHESIS_SYSTEM, synthesis_prompt)
    
    elapsed = time.time() - t0
    
    output = (
        f"### 🤖 ACTIVE CONSENSUS AGENT (V3)\n\n"
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
