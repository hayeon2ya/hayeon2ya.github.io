# ICU app integration

The homepage and navigation link to `/icu-app/`. The original Windows source is unchanged.
GitHub Pages serves the interface; model inference requires a separate Python server.
With no server configured, the interface explains the unavailable connection and disables inference.

## Run locally

From the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r icu_backend/requirements.txt
cd icu_backend
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/. Local serving uses same-origin API requests.
The dependency versions are copied from the original project and need installation verification.

## Deploy the Python service

Build from the repository root with `docker build -f Dockerfile.icu -t icu-app .`.
Run with `docker run --rm -p 8000:8000 icu-app` or deploy this Dockerfile on your Python/container host.
Set `ALLOWED_ORIGINS` to the exact homepage origin (comma-separated if multiple); default: `https://hayeon2ya.github.io`.
Model files are included under `icu_backend/runtime`; `MODEL_ROOT` can override that location.
The host must provide enough memory for PyTorch and the ten ensemble models.

After deployment, set `window.ICU_API_BASE_URL` in `icu-app/config.js` to the server's HTTPS URL, without a trailing slash.
Check `/api/health`, then submit a prediction and request a summary from the published interface.
Health reports application availability; the first prediction loads and verifies the model files.
Commit and push the website changes to the branch configured for GitHub Pages.

`icu_backend` is excluded from the generated Jekyll site. Files committed to a public repository are still publicly accessible through GitHub.
Do not add patient datasets or credentials. The copied runtime contains model weights, preprocessing artifacts, and training metadata only.
See `icu_backend/README.md` for the original feature-engineering limitations.
