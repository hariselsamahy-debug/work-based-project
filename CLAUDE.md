# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Smart-EHS: factory camera feeds → YOLO detection of PPE violations / fire / smoke / falls → real-time alerts → Claude writes an OSHA-referenced PDF incident report. The PPE model (YOLOv8n on Roboflow `sdp-lfigk/ppe-detection-ozhfb` v14, mAP50 0.883) was trained in a Colab notebook, `Untitled3.ipynb`, kept outside this repo because it contains a Roboflow API key. Its logic has been moved into `ml/`. More datasets are coming: fire/smoke, falls, and the OSHA PDFs.

## Commands

The Python venv is at `.venv`. It was created with `--system-site-packages` so it reuses the global torch/ultralytics install. Backend commands run from `backend/`, where `pytest.ini` sets `pythonpath = .` so `app` is importable.

```bash
# Backend
cd backend
../.venv/Scripts/python -m pytest                                  # all tests
../.venv/Scripts/python -m pytest tests/test_rules.py::test_missing_helmet_and_vest   # single test
../.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000

# Frontend (Vite dev server proxies /api and /ws to :8000)
cd frontend
npm run dev        # http://localhost:5173
npm run build      # tsc -b type-check + vite build — the only lint/type gate

# Training pipeline (see ml/datasets/README.md)
python ml/download.py --workspace <ws> --project <proj> --version <n>   # reads ROBOFLOW_API_KEY from .env
python ml/preprocess.py --src ml/datasets/X --dst ml/datasets/X-PREPROCESSED
python ml/validate_labels.py ml/datasets/X-PREPROCESSED
python ml/train.py --data ml/configs/<task>.yaml --name <task>          # then copy runs/<task>/weights/best.pt -> models/<task>.pt

# Everything in containers
docker compose up --build   # frontend on :8080 (nginx proxies to backend)
```

The shell is Windows. Python output containing Arabic or emoji needs `PYTHONIOENCODING=utf-8`.

## Architecture

The data flow crosses several modules in `backend/app/`:

1. **`vision/camera.py` `CameraStream`**: one thread per camera. It keeps only the latest frame. Video files loop at their native FPS so they behave like live feeds.
2. **`vision/pipeline.py` `CameraWorker`**: one thread per camera, running at `INFER_FPS`.
   - Each frame goes through the detectors, then `rules.evaluate`, then `annotate`. The annotated JPEG is cached for the MJPEG endpoint.
   - The frame then goes to `EventTracker.update`. When an alert fires, it calls the `on_alert` callback.
   - `CameraManager` builds everything from `cameras.yaml`.
3. **`vision/detectors.py`**: one `YoloDetector` per model, shared by all cameras and serialized with a lock. If a detector's weights file is missing, it is skipped with a warning; the app still starts.
4. **`vision/rules.py`: the core logic.**
   - The PPE dataset only labels items that are *present*. There is no "no helmet" class.
   - A violation (`NO_HARDHAT`, `NO_VEST`, …) means a `Person` box has no required item whose center lies in that item's body band (`PPE_REGIONS`, given as fractions of person height).
   - Labels from other models (fire/smoke/fall) become violations through `HAZARD_LABELS`, which matches case-insensitively.
   - `SEVERITY` maps each violation type to a severity.
5. **`vision/tracker.py`**:
   - Debounce: a violation type must be present for N consecutive frames per camera before it alerts.
   - Cooldown: after an alert, the same camera and type stay silent for a set time.
   - The tracker is shared across worker threads and guarded by a lock.
6. **`alerts.py`**:
   - `AlertRecorder` runs on worker threads. It saves the snapshot, inserts an `Incident` row, and pushes to the WebSocket through `AlertHub.broadcast_from_thread`.
   - That method uses `run_coroutine_threadsafe` on the event loop captured in `main.py`'s lifespan.
7. **`reports/service.py` `ReportService.build`**, called by `POST /api/incidents/{id}/report`:
   - `violation_map.describe` provides the title, standards and search query.
   - `OshaIndex` (BM25 over `data/osha/*.pdf|txt`) supplies text chunks.
   - `llm.write_report` produces a structured `IncidentReport`. It uses Claude via `client.beta.messages.parse(output_format=IncidentReport, fallbacks="default")`.
   - `pdf.render_pdf` (reportlab) renders the PDF.
   - The PDF path is cached in `Incident.report_path`.
   - Without `ANTHROPIC_API_KEY`, `template_report` is used instead.

Shared state hangs off `app.state` (`cameras`, `hub`, `reports`), and API routers read it from there.

**Config.** `config.py` `Settings` reads env/`.env`: `ANTHROPIC_API_KEY`, `CLAUDE_MODEL` (default `claude-opus-5-5`), `DB_URL`, `STORAGE_DIR`, `CAMERAS_FILE`, `DEVICE`, `INFER_FPS`, `STREAM_FPS`. `backend/app/cameras.yaml` defines detectors, `rules` (required PPE, debounce, cooldown) and cameras. Relative paths in it are resolved against the repo root by `load_site_config`.

**DB.** SQLAlchemy, one `incidents` table, SQLite by default in `storage/`. There are no migrations; `create_all` runs at startup. SQLite drops the timezone on read, so use `Incident.created_at_utc`, not `created_at`.

**Frontend** (`frontend/src`). It is React + TypeScript with no router and no state library.
- `App.tsx` switches between two pages, `LiveMonitoring` and `AlertsLog`, and owns the WebSocket subscription (`useAlertsSocket`), toasts and the alarm sound.
- All backend calls go through `api.ts`.
- Camera tiles are `<img>` tags pointed at the MJPEG endpoint.
- Violation display names live in `VIOLATION_LABELS` in `api.ts`.

## Adding a new detection model (fire/smoke, fall)

1. Train it and copy the weights to `models/<task>.pt`.
2. Uncomment or add the detector under `detectors:` in `cameras.yaml`, and add it to each camera's `detectors` list.
3. If its class names aren't already in `HAZARD_LABELS`, add them there and to `SEVERITY`.
4. Add an entry in `reports/violation_map.py` (OSHA standards + search query).
5. Add a label in the frontend `VIOLATION_LABELS`.

The rules tests use synthetic `Detection` boxes and need no model weights. Keep new rule logic testable the same way.

## Notes

- `models/ppe.pt` is committed (6.5 MB). Other `models/*.pt`, `storage/`, `data/samples/*` and `.env` are gitignored.
- Never commit `Untitled3.ipynb`: cell 1 has a hard-coded Roboflow API key (should be rotated). New code reads keys only from `.env`.
