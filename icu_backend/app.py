import os, sys, json
from pathlib import Path
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from clinical import OUTCOMES, HORIZONS, build_payload, validate_payload, validate_generated_text, deterministic_summary

APP_DIR = Path(__file__).resolve().parent
ROOT = Path(os.getenv('MODEL_ROOT', str(APP_DIR / 'runtime'))).resolve()
sys.path.insert(0, str(ROOT))
app = FastAPI(title='ICU Longitudinal Prediction Review', docs_url='/api/docs')

allowed_origins = [origin.strip() for origin in os.getenv(
    'ALLOWED_ORIGINS', 'https://hayeon2ya.github.io'
).split(',') if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins,
                   allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

class InferenceRequest(BaseModel):
    patient_id: int = Field(gt=0)
    decision_min: int = Field(ge=0)
    current_state: int = Field(ge=0, le=3)
    static: dict = {}
    events: list[dict] = []
    clinical_context: dict | None = None
    previous_prediction: dict | None = None
class InterpretRequest(BaseModel): payload: dict

class Ensemble:
    def __init__(self): self.loaded=False
    @staticmethod
    def _state(x):
        if isinstance(x,dict):
            for key in ('model_state_dict','state_dict','model'):
                if isinstance(x.get(key),dict): return x[key]
            if x and all(hasattr(v,'shape') for v in x.values()): return x
        raise RuntimeError('Unsupported checkpoint format: state dictionary not found.')
    def load(self):
        if self.loaded: return
        try:
            import torch
            from model import build_primary_model, build_transition_model
        except Exception as e: raise RuntimeError(f'Inference dependencies unavailable: {e}')
        self.torch=torch
        self.manifest=json.loads((ROOT/'FINAL_CV5_ENSEMBLE_MODEL.json').read_text())
        self.primary=[]; self.transition=[]
        for i in range(1,6):
            p=build_primary_model(str(ROOT/'model_spec.json'))
            p.load_state_dict(self._state(torch.load(ROOT/f'fold_{i}/primary_best.pt',map_location='cpu',weights_only=False)));p.eval();self.primary.append(p)
            t=build_transition_model(str(ROOT/'model_spec.json'))
            t.load_state_dict(self._state(torch.load(ROOT/f'fold_{i}/transition_best.pt',map_location='cpu',weights_only=False)));t.eval();self.transition.append(t)
        self.loaded=True
    def predict(self, req):
        self.load()
        from preprocessing import load_artifacts, preprocess_static, preprocess_events, select_history, dynamic_collate
        art=load_artifacts(str(ROOT/'preprocessing_artifacts.json'))
        # Fail safely but permit partial research-entry data: missing numeric values retain training-time
        # median imputation plus explicit missingness indicators; binary defaults are 0; categories are <MISSING>.
        raw={c:None for c in art['numeric']}; raw.update({c:0 for c in art['binary']}); raw.update({c:'<MISSING>' for c in art['categorical']}); raw.update(req.static); raw['stay_id']=req.patient_id
        static=preprocess_static(pd.DataFrame([raw]),art)
        event_cols=['stay_id','event_name','event_type','event_value','time_from_landmark_min','event_unit','delta_event_min','delta_feature_min']
        ev=[]
        for x in req.events:
            y={c:x.get(c) for c in event_cols};y['stay_id']=req.patient_id;ev.append(y)
        events=preprocess_events(pd.DataFrame(ev,columns=event_cols),art) if ev else pd.DataFrame(columns=['stay_id','event_name_id','event_type_id','event_unit_id','event_value_scaled','event_value_missing','time_min','delta_event_log','delta_feature_log'])
        hist=select_history(events,req.patient_id,req.decision_min,256)
        spec=json.loads((ROOT/'model_spec.json').read_text()); row=static.iloc[0]
        item={'stay_id':req.patient_id,'decision_min':float(req.decision_min),'current_state':req.current_state,
          'static_cont':self.torch.tensor(row[spec['static_cont_columns']].to_numpy(dtype='float32')),
          'static_cat':self.torch.tensor([int(row[c+'_id']) for c in spec['categorical_variables']],dtype=self.torch.long),'seq_len':len(hist),
          'event_name':self.torch.tensor(hist['event_name_id'].to_numpy(dtype='int64')),'event_type':self.torch.tensor(hist['event_type_id'].to_numpy(dtype='int64')),
          'event_unit':self.torch.tensor(hist['event_unit_id'].to_numpy(dtype='int64')),'event_value':self.torch.tensor(hist['event_value_scaled'].to_numpy(dtype='float32')),
          'value_missing':self.torch.tensor(hist['event_value_missing'].to_numpy(dtype='float32')),'time_log':self.torch.tensor(hist['time_log'].to_numpy(dtype='float32')),
          'delta_event':self.torch.tensor(hist['delta_event_log'].to_numpy(dtype='float32')),'delta_feature':self.torch.tensor(hist['delta_feature_log'].to_numpy(dtype='float32'))}
        batch=dynamic_collate([item])
        with self.torch.no_grad():
            pp=np.mean([self.torch.sigmoid(m(batch)).detach().cpu().numpy()[0] for m in self.primary],axis=0)
            tt=np.mean([self.torch.sigmoid(m(batch)).detach().cpu().numpy()[0] for m in self.transition],axis=0)
        risks={o:{f'{h}h':float(pp[i*5+j]) for j,h in enumerate(HORIZONS)} for i,o in enumerate(OUTCOMES)}
        transitions={k:float(tt[i]) for i,k in enumerate(self.manifest['transitions'])}
        thresholds={o:{f'{h}h':risks[o][f'{h}h']>=self.manifest['primary_thresholds'][f'{o.lower()}_{h}h'] for h in HORIZONS} for o in OUTCOMES}
        return build_payload(req.patient_id,req.decision_min,req.current_state,risks,transitions,thresholds,req.clinical_context,req.previous_prediction)
ensemble=Ensemble()
@app.get('/')
def home(): return FileResponse(APP_DIR.parent/'icu-app/index.html')
@app.get('/config.js')
def config(): return FileResponse(APP_DIR.parent/'icu-app/config.js', media_type='application/javascript')
@app.get('/api/health')
def health(): return {'status':'ok','model_loaded':ensemble.loaded}
@app.post('/api/predict')
def predict(req:InferenceRequest):
    try: return ensemble.predict(req)
    except Exception as e: raise HTTPException(503,detail=str(e))
@app.post('/api/interpret')
def interpret(req:InterpretRequest):
    errors=validate_payload(req.payload)
    if errors: raise HTTPException(422,detail=errors)
    text=deterministic_summary(req.payload); issues=validate_generated_text(text,req.payload)
    if issues: raise HTTPException(500,detail=issues)
    return {'mode':'deterministic_safe_fallback','text':text}
