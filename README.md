# InsightOut

InsightOut is an AI-assisted analytics chat application for exploring ecommerce data.

**Live app:** [insightoutai.netlify.app](https://insightoutai.netlify.app/)

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

The backend uses Gemini for the agent and the public GA4 BigQuery dataset for
data. Create a Google Cloud service account with permission to run BigQuery
jobs, download its JSON key to the repository root as `gcp-key.json`, and make
sure billing is enabled on the project. The dataset itself is public, but
BigQuery still needs a project and credentials to execute queries.

Install the dependencies and create a repository-level `.env` from
`.env.example`:

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\Activate.ps1
pip install -r server/requirements.txt
cp .env.example .env                   # Windows: Copy-Item .env.example .env
```

Set `GEMINI_API_KEY` in `.env`. The example also points
`GOOGLE_APPLICATION_CREDENTIALS` at `./gcp-key.json`; the application uses
that path by default.

Run the API from the repository root with:

```bash
python -m uvicorn app.main:app --app-dir server --reload
```

With the backend running, open the Vite URL shown by `npm run dev`. Set
`VITE_API_URL` in `client/.env.local` if the API is not running at
`http://localhost:8000`.
