import json
from typing_extensions import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langgraph.graph import START, END, StateGraph
from assistant.configuration import Configuration, SearchAPI
from assistant.utils import deduplicate_and_format_sources, tavily_search, format_sources, perplexity_search, duckduckgo_search
from assistant.state import SummaryState, SummaryStateInput, SummaryStateOutput
from assistant.prompts import query_writer_instructions, summarizer_instructions, reflection_instructions
import logging
from datetime import datetime
import os
import sys
import atexit

# 日誌設置
global logger
def init_logger(log_name, log_file='log_file.log', max_bytes=1024*1024, backup_count=5):
    global logger
    if logger is None:
        logger = logging.getLogger(log_name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            file_handler = logging.FileHandler(log_file, 'w', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    return logger

def close_logger():
    global logger
    if logger is not None:
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        logger = None

# Nodes
def generate_query(state: SummaryState, config: RunnableConfig):
    """ Generate a query for web search """
    query_writer_instructions_formatted = query_writer_instructions.format(research_topic=state.research_topic)
    configurable = Configuration.from_runnable_config(config)
    llm_json_mode = ChatOllama(base_url=configurable.ollama_base_url, model=configurable.local_llm, temperature=0, format="json")
    result = llm_json_mode.invoke(
        [SystemMessage(content=query_writer_instructions_formatted),
         HumanMessage(content="Generate a query for web search: format: { query : XXXX }")]
    )
    query = json.loads(result.content)
    return {"search_query": query['query']}

def web_research(state: SummaryState, config: RunnableConfig):
    """ Gather information from the web """
    configurable = Configuration.from_runnable_config(config)
    if isinstance(configurable.search_api, str):
        search_api = configurable.search_api
    else:
        search_api = configurable.search_api.value

    if search_api == "tavily":
        search_results = tavily_search(state.search_query, include_raw_content=True, max_results=1)
        search_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=1000, include_raw_content=True)
    elif search_api == "perplexity":
        search_results = perplexity_search(state.search_query, state.research_loop_count)
        search_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=1000, include_raw_content=False)
    elif search_api == "duckduckgo":
        search_results = duckduckgo_search(state.search_query, max_results=3, fetch_full_page=configurable.fetch_full_page)
        search_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=1000, include_raw_content=True)
    else:
        raise ValueError(f"Unsupported search API: {configurable.search_api}")

    return {"sources_gathered": [format_sources(search_results)], 
            "research_loop_count": state.research_loop_count + 1, 
            "web_research_results": [search_str]}

def summarize_sources(state: SummaryState, config: RunnableConfig):
    """ Summarize the gathered sources """
    existing_summary = state.running_summary
    most_recent_web_research = state.web_research_results[-1]

    if existing_summary:
        human_message_content = (
            f"<User Input> \n {state.research_topic} \n <User Input>\n\n"
            f"<Existing Summary> \n {existing_summary} \n <Existing Summary>\n\n"
            f"<New Search Results> \n {most_recent_web_research} \n <New Search Results>"
        )
    else:
        human_message_content = (
            f"<User Input> \n {state.research_topic} \n <User Input>\n\n"
            f"<Search Results> \n {most_recent_web_research} \n <Search Results>"
        )

    configurable = Configuration.from_runnable_config(config)
    llm = ChatOllama(base_url=configurable.ollama_base_url, model=configurable.local_llm, temperature=0)
    result = llm.invoke(
        [SystemMessage(content=summarizer_instructions),
         HumanMessage(content=human_message_content)]
    )
    running_summary = result.content

    while "<think>" in running_summary and "</think>" in running_summary:
        start = running_summary.find("<think>")
        end = running_summary.find("</think>") + len("</think>")
        running_summary = running_summary[:start] + running_summary[end:]

    return {"running_summary": running_summary, "previous_summary": existing_summary}

def reflect_on_summary(state: SummaryState, config: RunnableConfig):
    """Reflect on the summary and generate a follow-up query."""
    configurable = Configuration.from_runnable_config(config)
    llm_json_mode = ChatOllama(base_url=configurable.ollama_base_url, model=configurable.local_llm, temperature=0, format="json")
    result = llm_json_mode.invoke(
        [SystemMessage(content=reflection_instructions.format(research_topic=state.research_topic)),
         HumanMessage(content=f"Identify a knowledge gap and generate a follow-up web search query based on our existing knowledge: {state.running_summary}")]
    )
    follow_up_query = json.loads(result.content)
    query = follow_up_query.get('follow_up_query')

    if not query:
        return {"search_query": f"Tell me more about {state.research_topic}"}
    return {"search_query": follow_up_query['follow_up_query']}

def finalize_summary(state: SummaryState, config: RunnableConfig):
    """Finalize the summary."""
    all_sources = "\n".join(source for source in state.sources_gathered)
    state.running_summary = f"## Summary\n\n{state.running_summary}\n\n### Sources:\n{all_sources}"
    
    configurable = Configuration.from_runnable_config(config)
    llm_json_mode = ChatOllama(base_url=configurable.ollama_base_url, model=configurable.local_llm, temperature=0, format="json")
    summary_content = "\n".join(state.web_research_results)
    
    summary_content += (
        "\n" + "依據以上內容，生成一篇大約可分成4段的4000字繁體中文文章，適合用於 YouTube 旁白。"
        "請以 JSON 格式返回，結構如下：{ 'article': '你的文章內容' }"
    )
    
    result = llm_json_mode.invoke(
        [SystemMessage(content=f"你是一位有經驗的 YouTuber，正在分析一個有關{state.research_topic}的內容。"),
         HumanMessage(content=summary_content)]
    )
    
    try:
        res = llm_json_mode.invoke(
        [      HumanMessage(content="依照以下內容, 建立一個與之相關的檔案名稱的主檔名(確認是檔案名稱可用的字元):"+ state.research_topic)]
        )
        
        
        # now = datetime.now().strftime("%Y%m%d_%H%M%S")
        # filename = f"summary_{now}.txt"
        print(f"files={res.content}")
        filename = res.content + ".txt"
        with open(filename, "w", encoding="utf-8") as f:
            for item in state.web_research_results:
                f.write(f"{item}\n\n")  # Write each item to the file, followed by a newline character (\n) to separate item)
        result_json = json.loads(result.content)
        state.article = result_json.get("article", "無法生成文章")
    except (json.JSONDecodeError, TypeError):
        state.article = "生成文章時發生錯誤，可能是 LLM 輸出格式不正確"

    return {"running_summary": state.running_summary, "article": state.article}

def route_research(state: SummaryState, config: RunnableConfig) -> Literal["finalize_summary", "web_research"]:
    """Route the research based on the follow-up query and summary convergence using LLM."""
    configurable = Configuration.from_runnable_config(config)
    max_loops_exceeded = state.research_loop_count >= int(configurable.max_web_research_loops)
    
    summary_converged = False
    if state.previous_summary and state.running_summary:
        llm_json_mode = ChatOllama(base_url=configurable.ollama_base_url, model=configurable.local_llm, temperature=0, format="json")
        prompt = (
            f"以下是兩段關於 '{state.research_topic}' 的總結內容。\n\n"
            f"前一次總結：\n{state.previous_summary}\n\n"
            f"當前總結：\n{state.running_summary}\n\n"
            f"請判斷這兩段總結在語義上是否已經足夠相似，表明知識已收斂。"
            f"返回 JSON 格式：{{ 'is_converged': true/false }}"
        )
        result = llm_json_mode.invoke(
            [SystemMessage(content="你是語義分析專家，能判斷文本內容的相似性。"),
             HumanMessage(content=prompt)]
        )
        try:
            result_json = json.loads(result.content)
            summary_converged = result_json.get("is_converged", False)
        except (json.JSONDecodeError, TypeError):
            summary_converged = False  # 若 LLM 輸出異常，默認為未收斂

    if max_loops_exceeded or summary_converged:
        return "finalize_summary"
    else:
        return "web_research"

# Add nodes and edges
builder = StateGraph(SummaryState, input=SummaryStateInput, output=SummaryStateOutput, config_schema=Configuration)
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("summarize_sources", summarize_sources)
builder.add_node("reflect_on_summary", reflect_on_summary)
builder.add_node("finalize_summary", finalize_summary)

builder.add_edge(START, "generate_query")
builder.add_edge("generate_query", "web_research")
builder.add_edge("web_research", "summarize_sources")
builder.add_edge("summarize_sources", "reflect_on_summary")
builder.add_conditional_edges("reflect_on_summary", route_research)
builder.add_edge("finalize_summary", END)

graph = builder.compile()