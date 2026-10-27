# Smart-EHS

Factory cameras → AI detection of PPE violations, fire/smoke and falls → instant alerts → an OSHA-referenced PDF incident report written by Claude.

## Architecture

```
Cameras (RTSP / webcam / video file)
   │  CameraStream: one thread per camera, keeps only the newest frame
   ▼
Detectors (YOLO)        models/ppe.pt  (+ fire_smoke.pt, fall.pt when trained)
   ▼
Rules engine            matches PPE items to each Person -> NO_HARDHAT, NO_VEST, ... ; FIRE / SMOKE / FALL
   ▼
Event tracker           debounce (N consecutive frames) + cooldown per camera × violation type
   ├──► annotated frame ──► MJPEG  GET /api/cameras/{id}/stream   (red = violation, green = OK)
   └──► alert ──► snapshot + DB row (incidents) ──► WebSocket /ws/alerts ──► dashboard toast + sound
                                                    │
Dashboard "Generate report" ──► POST /api/incidents/{id}/report
                                   OSHA text search (BM25 over data/osha/*.pdf)
                                   + Claude (snapshot image + metadata + OSHA excerpts) → structured report
                                   → PDF (reportlab), cached in storage/reports/
```

**Why a rules engine:** the PPE dataset only labels items that are *present* (Gloves, Hard_hat, Mask, Person, Safety_boots, Vest). There is no "no helmet" class, so a violation is decided by checking whether each Person box has a Hard_hat in its head region, a Vest on its torso, and so on. See [backend/app/vision/rules.py](backend/app/vision/rules.py).

## Layout

| Path | What |
|------|------|
| `ml/` | Training: `download.py`, `preprocess.py`, `validate_labels.py`, `train.py`, `configs/` (code moved from the Colab notebook) |
| `models/` | Trained weights the backend loads (`ppe.pt`, …) |
| `data/osha/` | OSHA regulation PDFs/TXT for report citations |
| `data/samples/` | Test videos for demo cameras |
| `backend/app/cameras.yaml` | Detectors, required PPE, debounce/cooldown, camera list |
| `backend/app/vision/` | Camera threads, detectors, rules, tracker, annotation, pipeline |
| `backend/app/reports/` | OSHA index, Claude call, PDF rendering |
| `backend/app/api/` | REST + MJPEG + WebSocket endpoints |
| `frontend/` | React dashboard: Live monitoring, Alerts log, report download |
| `storage/` | SQLite DB, snapshots, generated reports (created at runtime) |

## Setup

1. **Weights:** the trained PPE model is already in the repo at `models/ppe.pt`.
2. **Demo video:** put a construction/factory video at `data/samples/demo.mp4` (or change `source` in `cameras.yaml` to a webcam index `"0"` or an RTSP URL).
3. **OSHA text (optional):** put 29 CFR 1910 PDFs in `data/osha/`.
4. **Secrets:** `cp .env.example .env` and set `ANTHROPIC_API_KEY`. Without it, reports still generate from a fixed template.

```bash
# Backend (from the project root)
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on Linux/macOS)
pip install -r backend/requirements-dev.txt
cd backend
uvicorn app.main:app --reload --port 8000
pytest                            # rules + tracker tests

# Frontend (second terminal)
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

Or everything in Docker: `docker compose up --build` → http://localhost:8080

## Adding the next datasets

Fire/smoke and fall detection are already wired; they just need weights. Follow [ml/datasets/README.md](ml/datasets/README.md): train, copy `best.pt` to `models/<task>.pt`, uncomment the detector in `cameras.yaml`, and add it to each camera's `detectors` list. Detector labels named `fire`, `smoke` or `fall` become violations automatically (`HAZARD_LABELS` in `rules.py`).

## Report model

`CLAUDE_MODEL` in `.env` (default `claude-opus-5-5`). Server-side refusal fallback is enabled (`fallbacks="default"`), so if a safety classifier declines a request it is retried on Anthropic's recommended fallback model. For a cheaper model set `CLAUDE_MODEL=claude-sonnet-5-5`.

## Security note

The Colab notebook has a Roboflow API key hard-coded in it. Rotate that key in Roboflow and keep the new one only in `.env` (`ml/download.py` reads it from there).
