# Datasets

Each dataset trains one detector. The backend loads the resulting weights from `models/<task>.pt`
and the rules engine reads the class names straight from the model, so class names matter.

| Task | Source | Classes | Weights | Status |
|------|--------|---------|---------|--------|
| ppe | Roboflow `sdp-lfigk/ppe-detection-ozhfb` v14 | Gloves, Hard_hat, Mask, Person, Safety_boots, Vest | `models/ppe.pt` | trained (mAP50 0.883) |
| fire_smoke | TBD (e.g. Roboflow Smoke & Fire) | must contain `fire` / `smoke` (any case) | `models/fire_smoke.pt` | waiting for data |
| fall | TBD | must contain `fall` (any case) | `models/fall.pt` | waiting for data |
| OSHA text | 29 CFR 1910 PDFs | – | `data/osha/*.pdf` | waiting for files |

## Adding a new detection dataset
1. `python ml/download.py --workspace <ws> --project <proj> --version <n>` (reads `ROBOFLOW_API_KEY` from `.env`)
2. `python ml/preprocess.py --src ml/datasets/<NAME> --dst ml/datasets/<NAME>-PREPROCESSED`
3. `python ml/validate_labels.py ml/datasets/<NAME>-PREPROCESSED`
4. Write `ml/configs/<task>.yaml`, then `python ml/train.py --data ml/configs/<task>.yaml --name <task>`
5. Copy `runs/<task>/weights/best.pt` to `models/<task>.pt` and enable it in `backend/app/cameras.yaml`.
   If its class names are new hazards, add them to `HAZARD_LABELS` in `backend/app/vision/rules.py`.
