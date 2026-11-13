# Jaguars Club Assistant

## Run locally

From the project root, start the FastAPI backend:

```powershell
uv run uvicorn Backend.chat_api:app --reload --port 8001
```

In another terminal, start the React frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite. The frontend proxies `/api` requests to
the backend at `http://127.0.0.1:8001`. Configure the OpenAI API key and MySQL
connection variables in the project-root `.env` file.

