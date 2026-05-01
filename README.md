# SafeLink Inspector — Phishing Detection Web App
<!-- filepath: /Users/apple/ML_project2/README.md -->

SafeLink Inspector is a Flask-based phishing detection web application that analyzes websites (URL + page content) and/or manual feature inputs to classify whether a site is legitimate or phishing. It includes a feature extractor, ML model, a detailed threat-analysis UI, and a responsive static frontend hosted on Vercel with the ML backend hosted on a dedicated backend service (Render/Railway).

## Key Features
- URL scanner: fetches a page, extracts ~30 features, returns a prediction + confidence and per-feature reasons
- Manual mode: enter features manually for offline/blocked pages
- Risk-level mapping and human-readable badges (Likely Safe / Uncertain / Suspicious / Likely Phishing / High Risk Phishing)
- Trusted-domain override (force high-confidence Legitimate for known domains)
- Static frontend (Vercel) + backend API (Render) deployment pattern for reliability

## Tech Stack
- Backend: Python, Flask, gunicorn
- ML: scikit-learn (trained model stored in `final_model/`)
- Feature extraction: requests, BeautifulSoup
- Frontend: static HTML/CSS/JS served by Vercel
- Deployment: Render (backend), Vercel (frontend static + proxy)

## Repo Structure (important files)
- `app.py` — Flask app; endpoints: `/scan`, `/predict`, `/threat-analysis`, `/threat-scanner`
- `feature_extractor.py` — URL feature extraction logic
- `NetworkSecurity/...` — project ML utilities & model wrapper
- `final_model/` — model and preprocessor pickles (`model.pkl`, `preprocessor.pkl`)
- `static/` — static assets used by backend-rendered templates
- `static_site/` — static frontend published to Vercel (HTML + static/)
- `templates/` — Jinja templates (used by backend; kept for Render deploy)
- `vercel.json` — Vercel routing & proxy to backend
- `Dockerfile` — container image for local/containerized testing
- `Procfile` — `web: gunicorn app:app --bind 0.0.0.0:$PORT`
- `.dockerignore`, `requirements.txt`

## Quickstart — Local Development
1. Clone repo and create a virtual env:
   ```
   git clone <repo-url>
   cd ML_project2
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Ensure model files exist:
   ```
   ls -la final_model
   # expect: model.pkl, preprocessor.pkl
   ```
3. Run dev server:
   ```
   python app.py
   # or with gunicorn (recommended)
   pip install gunicorn
   PORT=8080 gunicorn app:app --bind 0.0.0.0:8080
   ```
4. Open:
   - Backend: `http://127.0.0.1:5000` (or :8080)
   - Static frontend pages: open files in `static_site/` or use Vercel deploy described below

## Docker (local test)
Build and run container (requires Docker / Colima on macOS older versions):
```
docker build -t phishing-app .
docker run --rm -p 8080:8080 phishing-app
# open http://127.0.0.1:8080
```

## Deployment (recommended production pattern)
We recommend separating frontend (Vercel) and backend (Render/Railway) to avoid serverless size/time limits.

1. Backend → Render
   - Ensure `Procfile` present: `web: gunicorn app:app --bind 0.0.0.0:$PORT`
   - Push code to GitHub and create a Render Web Service tied to the repo/branch `main`
   - Render Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - Note the backend URL (e.g., `https://networksecurity-xxxxx.onrender.com`)

2. Frontend → Vercel (static)
   - Put polished static pages in `static_site/` and assets under `static_site/static/`
   - Update `vercel.json` routes to proxy API endpoints to your Render backend:
     ```
     { "src": "/scan", "dest": "https://<YOUR_BACKEND>/scan" }
     ...
     ```
   - Deploy with: `npx vercel --prod` or via Vercel Dashboard (import repo)
   - Users interact with Vercel-hosted UI; form POSTs are proxied to backend.

Notes: Deploying the full ML backend as Vercel serverless often fails due to package + model size limits. The above architecture avoids that.

## Environment Variables
- (Render) No env required if `final_model/` committed. If you host models externally:
  - `MODEL_URL` — HTTP(S) URL to `model.pkl`
  - `PREPROCESSOR_URL` — HTTP(S) URL to preprocessor pickle
- (Vercel) Use Dashboard → Project → Environment Variables to set the same keys if frontend needs them.

## Trusted Domains Override
A trusted-domain list is included in `app.py`. If a scanned URL matches any trusted domain, the app forces the prediction to `Legitimate` with confidence >= 95%. Edit the lists in `app.py` if you need to add/remove domains.

## Troubleshooting
- 500 on startup: check `requirements.txt` and that `final_model/*.pkl` exist and are readable.
- Vercel build error about bundle size: move ML backend to Render/Railway and publish only static frontend to Vercel.
- Slow initial scan: remote fetching and model loading may cause latency. Consider caching or using a persistent backend instance.

## Contribution
- Create issues for bugs or feature requests.
- Fork -> branch -> PR with clear description and tests where applicable.
- Keep model/data artifacts out of PRs larger than GitHub limits; use Git LFS or external storage.

## License
Specify license here (e.g., MIT) and add a `LICENSE` file.

---

If you want, I can:
- Generate a more detailed architecture diagram and sequence for request flow,
- Produce polished static HTML versions of all templates in `static_site/` ready for Vercel,
- Or create a small CI workflow to auto-deploy frontend/backend on push. Which would you like next?