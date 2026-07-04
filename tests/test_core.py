import unittest
from unittest.mock import patch, MagicMock
from agent_task.prompts import (
    BASE_SYSTEM,
    CRITIQUE_SYSTEM_TEMPLATE,
    get_critique_prompt,
    SYNTHESIS_SYSTEM,
    get_synthesis_prompt
)
from agent_task.core import agent_task, run_agent_query

class TestAgentTaskPrompts(unittest.TestCase):
    def test_get_critique_prompt(self):
        task = "Test Task"
        drafts = "Draft 1\nDraft 2"
        prompt = get_critique_prompt(task, drafts)
        self.assertIn("Test Task", prompt)
        self.assertIn("Draft 1", prompt)

    def test_get_synthesis_prompt(self):
        task = "Test Task"
        compilation = "Comp 1"
        prompt = get_synthesis_prompt(task, compilation)
        self.assertIn("Test Task", prompt)
        self.assertIn("Comp 1", prompt)

class TestAgentTaskCore(unittest.TestCase):
    @patch('agent_task.core.get_openai_client')
    def test_run_agent_query_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Respon Model"
        mock_client.chat.completions.create.return_value = mock_response

        res = run_agent_query("test-model", "sys", "user")
        self.assertEqual(res, "Respon Model")
        mock_client.chat.completions.create.assert_called_once()

    @patch('agent_task.core.get_openai_client')
    def test_run_agent_query_failure(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")

        res = run_agent_query("test-model", "sys", "user")
        self.assertIn("Error:", res)
        self.assertIn("API error", res)

    @patch('agent_task.core.run_agent_query')
    def test_agent_task_flow(self, mock_query):
        # We need mock_query to return different responses for different steps.
        # It's called:
        # Phase 1: 3 times (agent1, agent2, agent3 initial query)
        # Phase 2: 3 times (agent1, agent2, agent3 critique)
        # Phase 3: 1 time (agent1 synthesis)
        mock_query.side_effect = [
            # Phase 1
            "Draf 1", "Draf 2", "Draf 3",
            # Phase 2
            "Kritik 1", "Kritik 2", "Kritik 3",
            # Phase 3
            "Konsensus Akhir"
        ]

        result = agent_task(
            task="Test task",
            model1="m1",
            model2="m2",
            model3="m3"
        )

        self.assertIn("### 🤖 PROSES MULTI-AGENT COLLABORATION", result)
        self.assertIn("Konsensus Jawaban Akhir", result)
        self.assertIn("Konsensus Akhir", result)
        self.assertEqual(mock_query.call_count, 7)

if __name__ == '__main__':
    unittest.main()
