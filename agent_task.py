import os
import json
import logging
import threading
from typing import Dict, List, Any, Optional
import openai

# Fallback default models if user doesn't specify any
DEFAULT_MODEL1 = os.getenv("AGENT_TASK_MODEL1", "ag/claude-opus-4-6-thinking")
DEFAULT_MODEL2 = os.getenv("AGENT_TASK_MODEL2", "ag/gemini-3-flash-agent")
DEFAULT_MODEL3 = os.getenv("AGENT_TASK_MODEL3", "ag/claude-sonnet-4-6")

# This file is also maintained in the repo to serve as a clean single-file entrypoint or legacy wrapper if anyone runs it directly.
from agent_task.core import agent_task

if __name__ == "__main__":
    import sys
    test_task = sys.argv[1] if len(sys.argv) > 1 else "Jelaskan apa itu database PostgreSQL secara singkat."
    
    # We support custom models via environment variables if run from CLI, or can be passed to the python function.
    print(agent_task(
        task=test_task,
        model1=os.getenv("AGENT_TASK_MODEL1"),
        model2=os.getenv("AGENT_TASK_MODEL2"),
        model3=os.getenv("AGENT_TASK_MODEL3")
    ))
