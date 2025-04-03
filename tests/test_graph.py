import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from assistant.graph import finalize_summary, SummaryState, RunnableConfig

class TestFinalizeSummary(unittest.TestCase):

    def setUp(self):
        self.state = SummaryState(
            research_topic="The impact of artificial intelligence on healthcare",
            search_query="",
            sources_gathered=[],
            running_summary="",
            research_loop_count=0,
            web_research_results=[]
        )
        self.config = RunnableConfig(
            configurable={
                "ollama_base_url": "http://localhost:11434",
                "local_llm": "llama3",
                "search_api": "duckduckgo",
                "max_web_research_loops": "2",
                "fetch_full_page": False
            }
        )

    @patch.object(SummaryState, 'running_summary', new_callable=PropertyMock)
    @patch.object(SummaryState, 'sources_gathered', new_callable=PropertyMock)
    def test_finalize_summary(self, mock_sources_gathered, mock_running_summary):
        mock_sources_gathered.return_value = ["source1", "source2"]
        mock_running_summary.return_value = "This is a summary"

        result = finalize_summary(self.state, self.config)

        self.assertEqual(result['running_summary'], "## Summary\n\nThis is a summary\n\n### Sources:\nsource1\nsource2")

if __name__ == "__main__":
    unittest.main()