import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
from langchain_core.messages import AIMessage
import logging
from datetime import datetime

# 確保可以正確導入 graph.py
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from assistant import graph
from assistant.state import SummaryState
from assistant.configuration import Configuration, SearchAPI
from graph import init_logger, close_logger
# 模擬 graph 模組中的 logger
class MockGraphModule:
    def __init__(self):
        self.logger = None

mock_graph_module = MockGraphModule()

# 替代原本的 init_logger 函數
def mock_init_logger(log_name="research_logger", log_file=None, max_bytes=1024*1024, backup_count=5):
    
    if log_file is None:
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"research_log_{current_time}.log"
    
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, 'w', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    mock_graph_module.logger = logger
    return logger

# 替代原本的 close_logger 函數
def mock_close_logger():
    if mock_graph_module.logger is not None:
        for handler in mock_graph_module.logger.handlers:
            handler.close()
            mock_graph_module.logger.removeHandler(handler)
        mock_graph_module.logger = None

# 測試類
class TestResearchAutomation(unittest.TestCase):
    def setUp(self):
        self.state = SummaryState(
            research_topic="The impact of artificial intelligence on healthcare",
            search_query="",
            sources_gathered=[],
            running_summary="",
            research_loop_count=0,
            web_research_results=[]
        )
        
        self.config = {"configurable": {
            "ollama_base_url": "http://localhost:11434",
            "local_llm": "llama3",
            "search_api": "duckduckgo",
            "max_web_research_loops": "2",
            "fetch_full_page": False
        }}
        
        self.init_logger_patcher = patch.object(graph, 'init_logger', side_effect=mock_init_logger)
        self.close_logger_patcher = patch.object(graph, 'close_logger', side_effect=mock_close_logger)
        self.logger_patcher = patch.object(graph, 'logger', mock_graph_module.logger)
        
        self.mock_init_logger = self.init_logger_patcher.start()
        self.mock_close_logger = self.close_logger_patcher.start()
        self.mock_logger = self.logger_patcher.start()

    def tearDown(self):
        self.init_logger_patcher.stop()
        self.close_logger_patcher.stop()
        self.logger_patcher.stop()
        
        if mock_graph_module.logger is not None:
            mock_close_logger()

    @patch.object(graph, 'ChatOllama')
    @patch.object(graph, 'tavily_search')
    @patch.object(graph, 'perplexity_search')
    @patch.object(graph, 'duckduckgo_search')
    def test_full_research_workflow(self, mock_duckduckgo, mock_perplexity, mock_tavily, mock_chat_ollama):
        mock_llm_instance = MagicMock()
        mock_llm_json_instance = MagicMock()
        
        mock_llm_json_instance.invoke.return_value = AIMessage(content=json.dumps({"query": "AI healthcare applications"}))
        mock_search_results = [
            {"title": "AI in Healthcare", "url": "https://example.com/1", "content": "AI is revolutionizing healthcare."},
            {"title": "Medical AI", "url": "https://example.com/2", "content": "Medical diagnostics using AI."}
        ]
        mock_duckduckgo.return_value = mock_search_results
        mock_llm_instance.invoke.return_value = AIMessage(content="AI is being used in healthcare for diagnostics and treatment planning.")
        mock_llm_json_instance.invoke.side_effect = [
            AIMessage(content=json.dumps({"follow_up_query": "AI ethics in healthcare"})),
            AIMessage(content=json.dumps({"follow_up_query": "Future of AI in personalized medicine"}))
        ]
        
        mock_chat_ollama.side_effect = [mock_llm_json_instance, mock_llm_instance, mock_llm_json_instance]
        
        from assistant.graph import generate_query, web_research, summarize_sources, reflect_on_summary, finalize_summary
        
        query_result = generate_query(self.state, self.config)
        self.assertEqual(query_result["search_query"], "AI healthcare applications")
        
        self.state.search_query = query_result["search_query"]
        
        web_result = web_research(self.state, self.config)
        self.assertEqual(len(web_result["sources_gathered"]), 1)
        self.assertEqual(web_result["research_loop_count"], 1)
        
        self.state.sources_gathered = web_result["sources_gathered"]
        self.state.research_loop_count = web_result["research_loop_count"]
        self.state.web_research_results = web_result["web_research_results"]
        
        summary_result = summarize_sources(self.state, self.config)
        self.assertEqual(summary_result["running_summary"], "AI is being used in healthcare for diagnostics and treatment planning.")
        
        self.state.running_summary = summary_result["running_summary"]
        
        reflect_result = reflect_on_summary(self.state, self.config)
        self.assertEqual(reflect_result["search_query"], "AI ethics in healthcare")
        
        final_result = finalize_summary(self.state)
        self.assertTrue("## Summary" in final_result["running_summary"])
        self.assertTrue("### Sources:" in final_result["running_summary"])
        
        self.mock_init_logger.assert_called()
        self.mock_close_logger.assert_called()

    def test_graph_structure(self):
        from assistant.graph import graph as research_graph
        edges = list(research_graph.graph.edges)  # 修正 `transitions` 問題
        self.assertTrue(any(edge[0] == "reflect_on_summary" for edge in edges))

if __name__ == "__main__":
    unittest.main()
