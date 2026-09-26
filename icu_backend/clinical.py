import re
from copy import deepcopy

OUTCOMES=("AKI","ARF","Both","Death","Discharge")
HORIZONS=(3,12,24,48,72)
ELIGIBLE={"AKI":{0,2},"ARF":{0,1},"Both":{0,1,2},"Death":{0,1,2,3},"Discharge":{0,1,2,3}}
STATE_LABEL={0:"Neither AKI nor ARF",1:"AKI only",2:"ARF only",3:"Both AKI and ARF"}
ALLOWED={0:["0_to_1","0_to_2","0_to_3","0_to_4","0_to_5"],1:["1_to_3","1_to_4","1_to_5"],2:["2_to_3","2_to_4","2_to_5"],3:["3_to_4","3_to_5"]}
BANNED=re.compile(r"\b(start|stop|give|administer|prescribe|order|treat|dialy[sz]e|diagnos(?:e|is)|caused by|because of)\b",re.I)

def pct(x): return f"{x*100:.1f}%" if x < .01 else f"{x*100:.0f}%"
def valid_p(x): return isinstance(x,(int,float)) and 0 <= x <= 1

def validate_payload(p):
    errors=[]; state=p.get("current_state",{}).get("code")
    if state not in ALLOWED: errors.append("current_state.code must be 0, 1, 2, or 3")
    for outcome in OUTCOMES:
        rs=p.get("predicted_risk",{}).get(outcome,{})
        for h in HORIZONS:
            if not valid_p(rs.get(f"{h}h")): errors.append(f"Missing/invalid {outcome}.{h}h")
    for tr in ALLOWED.get(state,[]):
        if not valid_p(p.get("transition_probability_3h",{}).get(tr)): errors.append(f"Missing/invalid transition {tr}")
    return errors

def build_payload(patient_id, decision_min, state, risks, transitions, thresholds, clinical_context=None, previous=None):
    if state not in ALLOWED: raise ValueError("Terminal states cannot receive prediction inference")
    r={}; registry=[]
    for outcome in OUTCOMES:
        r[outcome]={}
        for h in HORIZONS:
            v=float(risks[outcome][f"{h}h"]); r[outcome][f"{h}h"]=v
            registry.append({"evidence_id":f"risk.{outcome}.{h}h","value":v,"display_percent":pct(v),"type":"primary_probability","eligible":state in ELIGIBLE[outcome]})
    tp={k:float(transitions[k]) for k in ALLOWED[state]}
    for k,v in tp.items(): registry.append({"evidence_id":f"transition.{k}.3h","value":v,"display_percent":pct(v),"type":"transition_probability","eligible":True})
    flags={o:{f"{h}h":bool(thresholds[o][f"{h}h"]) for h in HORIZONS} for o in OUTCOMES}
    return {"schema_version":"icu-generative-interpretation.v1","patient_id":str(patient_id),"decision_time":{"decision_min_from_landmark":int(decision_min),"decision_hours_from_landmark":decision_min/60,"landmark_definition":"ICU admission plus 6 hours"},"current_state":{"code":state,"label":STATE_LABEL[state],"interpretation_constraint":"Cumulative event-history state; not recovery or current physiologic severity."},"eligibility":{o:state in ELIGIBLE[o] for o in OUTCOMES},"predicted_risk":r,"threshold_flags":flags,"transition_probability_3h":tp,"transition_constraints":{"allowed_transition_ids":ALLOWED[state]},"previous_prediction": previous or {"available":False},"recent_clinical_context":clinical_context or {"available":False,"observed_items":[],"unavailable_domains":[]},"numeric_evidence_registry":registry,"model_metadata":{"threshold_warning":"F1-maximizing development operating points, not clinical cutoffs.","external_validation_status":"Not yet externally validated","transition_warning":"Rare transition probabilities may have imperfect absolute calibration."},"interpretation_policy":{"language":"en","trend_reporting_min_absolute_change":.05}}

def deterministic_summary(p):
    s=p['current_state']['code']; r=p['predicted_risk']; e=p['eligibility']; ts=p['transition_probability_3h']
    lines=[f"Assessment at {p['decision_time']['decision_hours_from_landmark']:g} hours after the 6-hour landmark. Cumulative state: {p['current_state']['label']}."]
    focus=[]
    for o in OUTCOMES:
        if e[o]: focus.append(f"{o}: {pct(r[o]['3h'])} within 3h; {pct(r[o]['24h'])} within 24h")
    lines.append("Model probabilities — " + "; ".join(focus) + ".")
    lines.append("Allowed next-3-hour transitions — " + "; ".join(f"{k}: {pct(v)}" for k,v in ts.items()) + ".")
    lines.append("These are model predictions, not observed events or diagnoses. Threshold flags are model-defined statistical operating points, not clinical cutoffs. Rare transitions and external validity require cautious interpretation.")
    return "\n\n".join(lines)

def validate_generated_text(text,payload):
    issues=[]
    if BANNED.search(text): issues.append("Contains diagnostic, causal, or treatment language")
    allowed={x['display_percent'] for x in payload['numeric_evidence_registry']}
    for x in re.findall(r"\b\d+(?:\.\d+)?%",text):
        if x not in allowed: issues.append(f"Unsupported percentage: {x}")
    for transition in re.findall(r"\b[0-3]_to_[1-5]\b",text):
        if transition not in payload['transition_constraints']['allowed_transition_ids']: issues.append(f"Impossible transition: {transition}")
    return issues
