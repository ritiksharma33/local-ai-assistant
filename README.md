

# 🧠 Local AI Assistant Platform

A full-stack, hardware-optimized orchestration platform for running and managing Smaller Language Models (SLMs) entirely locally. Built specifically to maximize performance on constrained Unified Memory architectures (e.g., Apple Silicon M1 8GB) without triggering system-locking disk swaps.


https://github.com/user-attachments/assets/48455c00-0e22-42af-90ed-89b338ce1fa7






## 🚀 Overview

This platform acts as a custom local API gateway and interactive client for LLMs. It wraps the Ollama engine in an async FastAPI backend, providing advanced routing pipelines, structured telemetry, and—most importantly—an **Active Memory Guardrail** that safely manages VRAM allocations when hot-swapping heavy parameter models.

### 🔑 Key Features

* **Active Memory Guardrail:** Synchronously inspects Mac physical RAM (`ollama.ps()`) and forcefully ejects stale models (`keep_alive=0`) before loading new weights, preventing OS swap-freezes.
* **Auto-Idle Optimization:** Implements a strict 2-minute `keep_alive` timer on all inferences to instantly reclaim system memory when you step away.
* **Multi-Pipeline Routing:**
* ⚡ **Stream (SSE):** Live token generation with connection-drop safety.
* ⚙️ **Standard (Buffered):** Full text compilation for bulk tasks.
* ✨ **Agentic:** Dynamic tool-calling loop execution.
* 📋 **Structured:** JSON-enforced validation engine.


* **Deep Telemetry Dashboard:** A real-time React/Recharts dashboard that tracks inference history, execution latency (sec), and exact token throughput (t/s) directly from a local SQLite database.

---

## 🛠️ Technology Stack

**Backend:**

* Python 3.13
* FastAPI & Uvicorn (Async ASGI server)
* HTTPX (Async client for Ollama API)
* SQLAlchemy (Async SQLite database)
* Pydantic (Strict schema enforcement)

**Frontend:**

* React 18 & Vite
* Tailwind CSS (Styling)
* Recharts (Data visualization)
* Lucide React (Iconography)
* React Markdown (Response rendering)

---

## 📦 Prerequisites

Before installing, ensure you have the following running on your machine:

1. [Node.js](https://nodejs.org/) (v18+)
2. [Python](https://www.python.org/) (3.13+)
3. [Ollama](https://ollama.ai/) installed and running as a background service.
4. Required local models pulled via your terminal:
```bash
ollama pull llama3.2
ollama pull dolphin-llama3

```



---

## ⚙️ Installation & Setup

### 1. Backend Setup

Navigate to the backend directory, create a virtual environment, and start the API server.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

```

*The API will be available at `http://127.0.0.1:8000*`

### 2. Frontend Setup

Open a new terminal window, navigate to the frontend directory, install dependencies, and start the Vite dev server.

```bash
cd frontend
npm install
npm run dev

```

*The UI will be available at `http://localhost:5173*`

---

## 🛡️ Architecture Deep Dive

### The Memory Guardrail Problem

Large language models consume massive amounts of RAM. Switching from a 3B model (Llama 3.2) to an 8B model (Dolphin) while the 3B model is still cached causes an 8GB M1 Mac to instantly run out of memory, triggering a severe system freeze as it swaps gigabytes of weights to the SSD.

**The Solution:**
Every endpoint is protected by `enforce_memory_guardrail(payload.model)`. Before any inference is sent to Ollama, FastAPI checks the active process state. If an unneeded model is sitting in RAM, it sends an empty prompt with `keep_alive=0` to instantly drop the weights from the unified memory pool, ensuring a clean slate for the incoming model.

### Telemetry & Streaming Capture

Streaming tokens via Server-Sent Events (SSE) traditionally breaks standard latency logging because the HTTP request stays open.
This architecture utilizes an internal asynchronous generator wrapper (`telemetry_tracked_stream_generator`) that counts yielded tokens in real-time. It catches `asyncio.CancelledError` for browser reloads, and uses a `finally` block to update the SQLite database with precision math once the socket successfully closes.

---

## 🗺️ Roadmap / Future Extensions

* [ ] **Conversational Memory buffer:** Refactor backend schemas to accept message arrays instead of single strings, allowing the agent to remember context across turns.
* [ ] **Local OS Tools:** Wire up Python scripts to the Agentic pipeline so the model can read local repositories, scan PDFs, and execute terminal commands.
* [ ] **Dynamic Model Discovery:** Auto-populate the frontend model dropdown by querying Ollama's `/api/tags` endpoint.

---

*Built with hardware discipline and local AI architecture.*
