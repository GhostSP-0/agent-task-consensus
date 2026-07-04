import sys
import argparse
from .core import agent_task

def main():
    parser = argparse.ArgumentParser(
        description="Run agent-task: a multi-agent consensus workflow."
    )
    parser.add_argument(
        "task",
        type=str,
        help="Task or prompt to execute across the multi-agent pool."
    )
    parser.add_argument(
        "--model1",
        type=str,
        default=None,
        help="Model for Agent 1 (and final synthesizer)."
    )
    parser.add_argument(
        "--model2",
        type=str,
        default=None,
        help="Model for Agent 2."
    )
    parser.add_argument(
        "--model3",
        type=str,
        default=None,
        help="Model for Agent 3."
    )

    args = parser.parse_args()
    
    try:
        result = agent_task(
            task=args.task,
            model1=args.model1,
            model2=args.model2,
            model3=args.model3
        )
        print(result)
        sys.exit(0)
    except Exception as e:
        print(f"Error running agent_task: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
