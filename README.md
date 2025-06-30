# 🌤️ MetroFlux — Multi-Agent LLM Weather Assistant

**MetroFlux** is an intelligent weather chatbot built using a multi-agent architecture and large language models. It interprets natural language queries, classifies user intent, resolves dates, fetches real-time or historical weather data, summarizes the results, and generates interactive visualizations using Plotly.

---

## 🔍 Key Features

- **Multi-Agent Architecture:** Modular agents handle routing, date resolution, summarization, and visualization.
- **Intent Detection & Tool Selection:** Dynamically chooses the appropriate weather tool (current, past, or future).
- **Date Resolution:** Parses temporal phrases like “this weekend” or “past 3 days” into ISO date ranges.
- **Location Awareness:** Resolves cities and regions into lat/lon coordinates using geolocation services.
- **LLM-Powered Summarization:** Uses structured prompt templates to generate concise weather reports.
- **Graph Generation:** Produces time-series Plotly visualizations when trends or patterns are present.
- **Frontend Integration:** React + Vite chat UI for real-time interaction.
- **CLI Integration:** Typer-based CLI for easy local execution and development.

---

## 🧰 Tech Stack

- **Python**, **FastAPI**, **LangChain**
- **Open-Meteo API** for weather data
- **Plotly (JSON)** for graph rendering
- **React + Vite** (Frontend)
- **Pydantic**, **Typer**, **uv** (Backend setup and CLI)

---

## 💡 Example Query

> “Will it rain in Bangalore next week?”

MetroFlux processes this by:
- Routing to the appropriate agent
- Resolving the temporal span
- Fetching weather data
- Summarizing with LLM
- Generating a temperature and precipitation chart (if relevant)

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/The-Gokul-Kishore/MetroFlux.git
cd MetroFlux
````

### 2. Install dependencies

```bash
pip install uv
uv sync
```

### 3. Set up environment variables

Create a `.env` file:

```dotenv
# === Required Environment Variables ===
MODEL_PROVIDER=google_genai
MODEL_NAME=gemini-1.5-flash

# API key for your selected provider (Google, OpenAI, etc.)
GOOGLE_API_KEY=your_api_key_here
# OR
OPENAI_API_KEY=your_openai_key_here
```

### 4. Set up the frontend

```bash
metroflux setup-frontend
```

### 5. Start the backend

```bash
.venv/Scripts/activate
metroflux run-backend
```

### 6. Start the frontend

```bash
metroflux run-frontend
```

---

## 📄 License

MIT License

---

## 👤 Author

Built by **Gokul Kishore**
[GitHub](https://github.com/The-Gokul-Kishore) • [LinkedIn](https://www.linkedin.com/in/your-link-here)

---
