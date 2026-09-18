# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:


# InsightOut

InsightOut is an AI-assisted analytics chat application for exploring ecommerce data.

## Structure

- `client/` - React frontend served by Vite
- `server/` - FastAPI backend and agent tools

## Frontend commands

```bash
npm install
npm run dev
npm run build
npm run lint
```

## Backend setup

Install the dependencies from `server/requirements.txt`, copy `.env.example` to `.env`, and provide the required API credentials. Run the API from the repository root with:

```bash
python -m uvicorn app.main:app --app-dir server --reload
```
