# Ollama Deep Researcher

Ollama Deep Researcher is a fully local web research assistant that uses any LLM hosted by [Ollama](https://ollama.com/search). It generates web search queries, gathers results, summarizes findings, identifies knowledge gaps, and iteratively improves the summary for a user-defined number of cycles. The final output is a markdown summary with all sources used.

## 🚀 Quickstart

### Windows

1. Download the Ollama app for Windows [here](https://ollama.com/download).

2. Pull a local LLM from [Ollama](https://ollama.com/search). For example:
```powershell
ollama pull deepseek-r1:8b
```

3. Clone the repository:
```powershell
git clone https://github.com/langchain-ai/ollama-deep-researcher.git
cd ollama-deep-researcher
```

4. (Recommended) Create a virtual environment:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

5. Install dependencies:
```powershell
pip install -e .
```

6. Launch the assistant:
```powershell
python app.py
```

### Folder-Based Video Creation

This feature allows users to process a folder containing `.mp3` and `.png` files to create videos. The system will:
1. Pair `.mp3` and `.png` files within subfolders.
2. Use `ffmpeg` to create individual video clips for each pair.
3. Optionally merge these clips into a single `.mp4` file with fade-in/out transitions.

#### How to Use
1. Open the application in your browser.
2. Use the `/process-folder` endpoint to submit a folder path and specify whether to generate a final concatenated video.
3. The processed videos will be saved in their respective subfolders, and the final video (if generated) will be saved in the root folder as `output.mp4`.

#### Example API Request
To process a folder and generate a final video:
```bash
curl -X POST http://localhost:9125/process-folder \
-H "Content-Type: application/json" \
-d '{
  "folderPath": "/path/to/folder",
  "generateFinalVideo": true
}'
```

#### Example Output
- Individual videos: Saved in their respective subfolders as `output.mp4`.
- Final concatenated video: Saved in the root folder as `output.mp4`.

### Notes
- Ensure subfolders contain `.mp3` and `.png` files.
- Files are processed in the order of their modification times.
- The `generateFinalVideo` option determines whether a final concatenated video is created.

## Outputs

The output is a markdown file containing the research summary, with citations to the sources used. All sources gathered during research are saved.

## How it works

1. Given a user-provided topic, the system uses a local LLM to generate a web search query.
2. It uses a search engine to find relevant sources.
3. The LLM summarizes the findings from the web search.
4. The LLM reflects on the summary, identifying knowledge gaps.
5. It generates a new search query to address the gaps.
6. The process repeats for a configurable number of iterations.

## Running as a Docker container

The Docker-based setup is no longer supported. Instead, the application now uses `dify` for deployment. Update your workflow to use the new `dify`-based setup.

## Deprecated Features

- **Docker-based deployment**: The previous Docker setup using `ollama` and `langchain` is no longer functional.
- **Unused API Endpoints**: Endpoints like `/save_mp3` and `/generate-and-save-images` are currently not in active use and may be removed in future updates.
