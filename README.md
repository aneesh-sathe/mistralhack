# Math Tutor MVP

LearnStral is a local-first MVP that ingests a PDF (any subject) and generates lesson modules with script, Manim animation, ElevenLabs narration, SRT captions, and final muxed MP4.

## Stack

- Frontend: Next.js (App Router), React, TypeScript, Tailwind, ShadCN-style UI components
- Backend: FastAPI, SQLAlchemy, Alembic
- Jobs: Redis + RQ worker
- DB: Postgres
- Storage: local filesystem mounted to `./data`
- Auth: Google OAuth + `DEV_AUTH_BYPASS=true`

## Environment setup

1. Copy env template:

```bash
cp .env.example .env
```

2. Fill values in `.env`:

- `JWT_SECRET`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `DEV_AUTH_BYPASS` (`false` by default; set `true` for bypass mode)
- `LLM_BASE_URL`
- `LLM_API_KEY`
- `CHAT_BASE_URL`
- `CHAT_API_KEY`
- `CHAT_MODEL` (explicit module-chat model, e.g. `mistral-small-latest`)
- `VLM_BASE_URL`
- `VLM_API_KEY`
- `VLM_ENABLED` (`false` by default)
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID`
- `ELEVENLABS_MODEL_ID`
- `DATABASE_URL`
- `REDIS_URL`

## Run (one command)

```bash
docker compose up --build
```

App URLs:

- Frontend: <http://localhost:3000>
- Backend API: <http://localhost:8000>

## Minimal demo path

1. Open <http://localhost:3000/login>
2. If using bypass mode, continue directly; otherwise click Google login.
3. Go to `/documents`, upload a PDF.
4. Wait for parse job to complete and open the document detail page.
5. Pick a module and click **Generate Lesson**.
6. When generation job completes, watch the video and synced captions on the module page.

## Tests

Backend tests run with fake providers and no external API calls:

```bash
cd backend
python -m pytest -q
```

Frontend smoke test:

```bash
cd frontend
npm test
```

## Notes

- SRT captions are segment-level only (no word karaoke).
- OCR fallback priority: PDF text extraction -> Tesseract OCR -> optional VLM OCR if enabled.
- Backend auto-runs `alembic upgrade head` on startup.

## Optional: Manim MCP Backend

You can route render execution through [manim-mcp-server](https://github.com/abhiemj/manim-mcp-server) instead of local `manim` CLI.

Set in `.env`:

- `MANIM_RENDER_BACKEND=mcp`
- `MANIM_MCP_COMMAND` (for example `python`)
- `MANIM_MCP_ARGS` (for example `/opt/manim-mcp-server/src/manim_server.py`)
- `MANIM_MCP_MEDIA_DIR` (for example `/opt/manim-mcp-server/src/media/manim_tmp`)
- `MANIM_MCP_TIMEOUT_SECONDS` (for example `240`)
- `MANIM_MCP_SERVER_DIR` (host path to cloned repo, default `./manim-mcp-server`)

Then clone the server repo in that mounted location (or point `MANIM_MCP_SERVER_DIR` to an existing checkout).

How it is used:

1. The backend still uses the LLM to generate Manim code.
2. The render step calls MCP tool `execute_manim_code` on `manim-mcp-server`.
3. The backend copies the generated MP4 from `MANIM_MCP_MEDIA_DIR` into app storage (`/data/video/{module_id}.mp4`).
