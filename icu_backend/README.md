# ICU longitudinal prediction web application

## User workflow
1. Enter de-identified patient baseline data, assessment time, and cumulative state.
2. Optionally paste a clinical note and use **문장으로부터 후보 event 추가**. Review every suggested event — note extraction is not model input by itself.
3. Review/add timestamped event rows and run **모델 예측 실행 및 결과 갱신**.
4. The right panel refreshes only with the returned CV5 model inference result. No client-side fabricated risk values are used.

## Runtime
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export MODEL_ROOT=./runtime
uvicorn app:app --host 127.0.0.1 --port 8000
```
Open `http://127.0.0.1:8000`.

## Important implementation limitation
The supplied preprocessing function accepts already engineered static features such as `lm_last_creatinine`, summary statistics, treatment doses/rates, and missingness. This research UI accepts raw events plus a subset of baseline inputs but does **not** recreate undocumented feature-engineering rules for every one of the 366 static inputs. Missing fields follow the supplied frozen preprocessing's median/missingness behavior. Production use requires your original feature-engineering pipeline or a verified EHR mapping service to populate all training-time features.

No free-text note is sent directly to the prediction model. It only helps populate reviewable candidate event rows.
