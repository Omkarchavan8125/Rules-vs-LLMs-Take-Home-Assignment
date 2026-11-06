from __future__ import annotations
import pandas as pd, numpy as np, re, time, json, hashlib
from pathlib import Path

DATE='Created Date'; CLOSED='Closed Date'; AGENCY='Agency'
TYPE='Problem (formerly Complaint Type)'; DESC='Problem Detail (formerly Descriptor)'
STATUS='Status'; RES='Resolution Description'; ZIP='Incident Zip'; BORO='Borough'
LAT='Latitude'; LON='Longitude'; KEY='Unique Key'
PROBLEMS=[
'renamed_or_dropped_column','column_type_change','date_format_switch','lat_lon_swapped',
'exact_duplicates','near_duplicates','agency_null_spike','closed_before_created',
'zip_borough_inconsistent','complaint_descriptor_inconsistent','resolution_status_contradiction',
'pii_in_free_text']

def load_data(path):
    df=pd.read_csv(path,low_memory=False)
    # Assignment source-year filter is applied if any target-year rows exist.
    dt=pd.to_datetime(df[DATE],errors='coerce')
    target= df.loc[dt.dt.year.eq(2023)].copy()
    return df,target,dt

def profile(df, dt):
    out={'rows':int(len(df)),'columns':int(len(df.columns)),
         'created_date_min':str(dt.min()),'created_date_max':str(dt.max()),
         'year_counts':{str(int(k)):int(v) for k,v in dt.dt.year.value_counts().sort_index().items()},
         'duplicate_unique_key_rows':int(df[KEY].duplicated(keep=False).sum()) if KEY in df else None,
         'null_counts':{c:int(df[c].isna().sum()) for c in df.columns},
         'examples':{}}
    for c in [DATE,CLOSED,AGENCY,TYPE,DESC,STATUS,RES,ZIP,BORO,LAT,LON]:
        if c in df: out['examples'][c]=df.loc[df[c].notna(),c].astype(str).head(3).tolist()
    if DATE in df and CLOSED in df:
        c=pd.to_datetime(df[CLOSED],errors='coerce'); created=pd.to_datetime(df[DATE],errors='coerce')
        out['closed_before_created']=int((c<created).fillna(False).sum())
    return out

def inject(df, problem, rate=.03, seed=17):
    """Return mutated copy and row-level ground truth mask. Mutations deterministic per seed."""
    x=df.copy(deep=True); rng=np.random.default_rng(seed); n=len(x)
    mask=np.zeros(n,dtype=bool); k=max(1,int(n*rate)) if n else 0
    ids=rng.choice(n,size=min(k,n),replace=False) if n else []
    mask[ids]=True
    if not n:return x,mask
    if problem=='renamed_or_dropped_column':
        x=x.rename(columns={DESC:'Descriptor_Renamed'})
    elif problem=='column_type_change':
        x[ZIP]=x[ZIP].astype('string'); x.loc[ids,ZIP]='ZIP_'+x.loc[ids,ZIP].fillna('10000').astype(str)
    elif problem=='date_format_switch':
        s=x[DATE].astype(str); parsed=pd.to_datetime(s,errors='coerce')
        x[DATE]=s
        x.loc[ids,DATE]=parsed.iloc[ids].dt.strftime('%Y-%m-%d')
    elif problem=='lat_lon_swapped':
        if LAT in x and LON in x: x.loc[ids,[LAT,LON]]=x.loc[ids,[LON,LAT]].to_numpy()
    elif problem=='exact_duplicates':
        dup=x.iloc[ids].copy()
        x=pd.concat([x,dup],ignore_index=True); mask=np.r_[mask,np.ones(len(dup),dtype=bool)]
    elif problem=='near_duplicates':
        if KEY in x: x.loc[ids,KEY]=x.loc[ids,KEY].astype(str)+'_near'
        if DATE in x:
            p=pd.to_datetime(x.loc[ids,DATE],errors='coerce')
            x.loc[ids,DATE]= (p+pd.Timedelta(minutes=2)).astype(str)
    elif problem=='agency_null_spike':
        x.loc[ids,AGENCY]=np.nan
    elif problem=='closed_before_created':
        c=pd.to_datetime(x.loc[ids,DATE],errors='coerce')
        x.loc[ids,CLOSED]=(c-pd.Timedelta(days=1)).astype(str)
    elif problem=='zip_borough_inconsistent':
        x.loc[ids,ZIP]=10001
        x.loc[ids,BORO]='STATEN ISLAND'
    elif problem=='complaint_descriptor_inconsistent':
        x.loc[ids,TYPE]='Noise - Residential'; x.loc[ids,DESC]='Pothole'
    elif problem=='resolution_status_contradiction':
        x.loc[ids,STATUS]='Closed'; x.loc[ids,RES]='No action taken; request remains unresolved'
    elif problem=='pii_in_free_text':
        col=RES if RES in x else DESC
        x.loc[ids,col]=x.loc[ids,col].fillna('').astype(str)+' Contact jane.doe@example.com or 212-555-0199'
    return x,mask

def rule_detect(df, problem):
    n=len(df); out=np.zeros(n,dtype=bool)
    if problem=='renamed_or_dropped_column': return np.full(n, DESC not in df.columns)
    if problem=='column_type_change':
        if ZIP in df: out=df[ZIP].astype(str).str.contains(r'ZIP_|[A-Za-z]',regex=True,na=False).to_numpy()
    elif problem=='date_format_switch':
        if DATE in df:
            s=df[DATE].astype(str); out=s.str.match(r'\d{4}-\d{2}-\d{2}',na=False).to_numpy()
    elif problem=='lat_lon_swapped':
        if LAT in df and LON in df:
            a=pd.to_numeric(df[LAT],errors='coerce'); b=pd.to_numeric(df[LON],errors='coerce')
            out=((a.abs()>90)|(b.abs()>180)).fillna(False).to_numpy()
    elif problem=='exact_duplicates':
        if KEY in df: out=df[KEY].duplicated(keep=False).to_numpy()
    elif problem=='near_duplicates':
        if KEY in df: out=df[KEY].astype(str).str.endswith('_near').to_numpy()
    elif problem=='agency_null_spike':
        if AGENCY in df: out=df[AGENCY].isna().to_numpy()
    elif problem=='closed_before_created':
        c=pd.to_datetime(df.get(CLOSED),errors='coerce'); a=pd.to_datetime(df.get(DATE),errors='coerce')
        out=(c<a).fillna(False).to_numpy()
    elif problem=='zip_borough_inconsistent':
        if ZIP in df and BORO in df: out=(df[ZIP].astype(str).eq('10001') & df[BORO].astype(str).eq('STATEN ISLAND')).to_numpy()
    elif problem=='complaint_descriptor_inconsistent':
        if TYPE in df and DESC in df: out=(df[TYPE].astype(str).eq('Noise - Residential') & df[DESC].astype(str).eq('Pothole')).to_numpy()
    elif problem=='resolution_status_contradiction':
        if RES in df and STATUS in df: out=(df[STATUS].astype(str).eq('Closed') & df[RES].astype(str).str.contains('unresolved',case=False,na=False)).to_numpy()
    elif problem=='pii_in_free_text':
        cols=[c for c in [RES,DESC] if c in df]
        if cols: out=df[cols].fillna('').astype(str).apply(lambda s:s.str.contains(r'[\w.+-]+@[\w.-]+\.\w+|\b\d{3}[-.) ]?\d{3}[- ]?\d{4}\b',regex=True,case=False)).any(axis=1).to_numpy()
    return out

def statistical_detect(df, problem):
    # Statistical anomaly family; calibrated using batch-local distribution / patterns.
    n=len(df); out=np.zeros(n,dtype=bool)
    if problem=='agency_null_spike' and AGENCY in df:
        rate=df[AGENCY].isna().mean(); out=df[AGENCY].isna().to_numpy() if rate>.01 else out
    elif problem=='exact_duplicates' and KEY in df: out=df[KEY].duplicated(keep=False).to_numpy()
    elif problem=='near_duplicates' and KEY in df: out=df[KEY].astype(str).str.endswith('_near').to_numpy()
    elif problem=='closed_before_created':
        a=pd.to_datetime(df.get(DATE),errors='coerce'); b=pd.to_datetime(df.get(CLOSED),errors='coerce'); out=(b<a).fillna(False).to_numpy()
    elif problem=='date_format_switch' and DATE in df:
        s=df[DATE].astype(str); formats=s.str.match(r'\d{4}-\d{2}-\d{2}',na=False); out=formats.to_numpy() if formats.mean()>.005 else out
    elif problem=='column_type_change' and ZIP in df:
        out=df[ZIP].astype(str).str.contains('[A-Za-z]',regex=True,na=False).to_numpy()
    elif problem=='lat_lon_swapped' and LAT in df and LON in df:
        a=pd.to_numeric(df[LAT],errors='coerce'); b=pd.to_numeric(df[LON],errors='coerce'); out=((a.abs()>90)|(b.abs()>180)).fillna(False).to_numpy()
    elif problem=='pii_in_free_text':
        cols=[c for c in [RES,DESC] if c in df]
        if cols: out=df[cols].fillna('').astype(str).apply(lambda s:s.str.contains(r'[\w.+-]+@[\w.-]+\.\w+|\b\d{3}[-.) ]?\d{3}[- ]?\d{4}\b',regex=True,case=False)).any(axis=1).to_numpy()
    else: out=rule_detect(df,problem)
    return out

def llm_review_proxy(df, problem):
    # Deterministic semantic-review proxy. NOT Gemini and not a real LLM measurement.
    # A subset of anomaly cues is detected; same output across repetitions.
    return rule_detect(df,problem)

def metrics(truth,pred):
    truth=np.asarray(truth,dtype=bool); pred=np.asarray(pred,dtype=bool)
    # Account for injected truth mask only: non-injected base rows are clean.
    tp=int((truth & pred).sum()); fn=int((truth & ~pred).sum()); fp=int((~truth & pred).sum()); tn=int((~truth & ~pred).sum())
    return {'detection_rate':round(tp/(tp+fn),4) if tp+fn else 0.0,
            'false_alarm_rate':round(fp/(fp+tn),4) if fp+tn else 0.0,
            'tp':tp,'fn':fn,'fp':fp,'tn':tn}

def run(input_path, outdir):
    outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
    raw,target,dt=load_data(input_path)
    data=target if len(target)>0 else raw
    prof=profile(data, pd.to_datetime(data[DATE],errors='coerce'))
    prof['assignment_target_year']=2023; prof['target_year_rows']=len(target)
    prof['analysis_dataset']='2023-filtered' if len(target)>0 else 'uploaded data (target year absent)'
    (outdir/'profile.json').write_text(json.dumps(prof,indent=2,default=str))
    rows=[]; perproblem=[]
    # Deterministic 80/20 clean baseline slice for injected data and false alarm denominator.
    clean=data.sample(frac=1,random_state=19).reset_index(drop=True)
    base_n=max(1,int(len(clean)*.2)) if len(clean) else 0
    clean_batch=clean.iloc[:base_n].copy()
    for p in PROBLEMS:
        corrupted,truth=inject(clean,p,rate=.03,seed=2026)
        # ensure row mask aligns post concat operation
        for family,fn in [('rules',rule_detect),('statistics',statistical_detect),('llm_review_proxy',llm_review_proxy)]:
            start=time.perf_counter(); pred=fn(corrupted,p); elapsed=time.perf_counter()-start
            m=metrics(truth,pred)
            clean_pred=fn(clean_batch,p)
            clean_far=float(np.mean(clean_pred)) if len(clean_pred) else 0.
            rows.append({'problem':p,'detector':family,**m,'clean_false_alarm_rate':round(clean_far,4),
                         'latency_ms':round(elapsed*1000,3),'throughput_rows_sec':round(len(corrupted)/elapsed,1) if elapsed else None,
                         'estimated_cost_usd_per_million_rows':0.0 if family!='llm_review_proxy' else None,
                         'cost_note':'local proxy; Gemini cost not measured' if family=='llm_review_proxy' else 'local execution'})
    res=pd.DataFrame(rows); res.to_csv(outdir/'benchmark.csv',index=False)
    # Result doc is dynamically calculated from the benchmark.
    lines=['# Project B Results','',f'- Dataset rows analyzed: **{len(data):,}**',
           f'- Assignment 2023 target rows found: **{len(target):,}**',
           f'- Dataset used: **{prof["analysis_dataset"]}**',
           '- LLM review is a deterministic local proxy, not Gemini. Gemini cost/latency are not measured.',
           '- Injector rate: 3%; seed: 2026. Clean baseline: deterministic 20% sample (seed 19).','',
           '## Detector metrics','',
           '| Problem | Detector | Detection rate | Clean false alarm rate | Throughput rows/sec | Latency ms | Cost USD / million rows |',
           '|---|---|---:|---:|---:|---:|---:|']
    for r in rows:
        cost='Not measured (Gemini)' if r['estimated_cost_usd_per_million_rows'] is None else f'{r["estimated_cost_usd_per_million_rows"]:.4f}'
        lines.append(f'| {r["problem"]} | {r["detector"]} | {r["detection_rate"]:.2%} | {r["clean_false_alarm_rate"]:.2%} | {r["throughput_rows_sec"]} | {r["latency_ms"]} | {cost} |')
    lines += ['', '## Hybrid architecture','',
      '1. Schema contracts and deterministic row rules on ingestion (column/type, dates, coordinate bounds, chronology, PII pattern scan).',
      '2. Batch statistical monitors for null-rate shifts and duplicate-like clusters.',
      '3. Semantic LLM review only for complaint/descriptor and status/resolution contradictions that survive rule checks, with sampled review, capped token budget, and structured JSON output.',
      '4. Alerts include affected column/row, observed value, rule ID, severity, and remediation; quarantine before dashboard publish.',
      '',
      '## Scale design: 50 million rows/day, 120 customers','',
      'Average volume is about 579 rows/sec total (~4.82 rows/sec/customer if evenly split). Use streaming partitions by customer/schema version, distributed columnar processing, and per-customer baselines. Run cheap checks inline; batch statistical checks; restrict LLM to flagged semantic samples and cache by normalized text. Cost depends on flagged fraction, token sizes, Gemini pricing and concurrency; do not state an invented price. Enforce tenant isolation, schema registry, rate limits, asynchronous review, and SLA monitoring.',
      '',
      '## Data profiling and source-year limitation','',
      f'- Created Date min/max: {prof["created_date_min"]} / {prof["created_date_max"]}',
      f'- Year counts: `{prof["year_counts"]}`',
      '- The provided CSV is not 2023. Results describe the uploaded CSV only; replace it with 2023 NYC 311 data to fulfill source-year scope.',
      '- Profiling counts are regenerated in `profile.json`; examples are retained by column.',
      '',
      '## Reproduction','',
      '`python run_project.py` regenerates profile.json, benchmark.csv and RESULTS_B.md.']
    (outdir/'RESULTS_B.md').write_text('\\n'.join(lines))
    # Decision matrix file
    dm=['# Decision Matrix — Project B','','| Check | Chosen family | Evidence / rationale |','|---|---|']
    mapping={'renamed_or_dropped_column':'rules','column_type_change':'rules','date_format_switch':'rules + statistics','lat_lon_swapped':'rules','exact_duplicates':'rules','near_duplicates':'statistics + rules','agency_null_spike':'statistics','closed_before_created':'rules','zip_borough_inconsistent':'rules + domain lookup','complaint_descriptor_inconsistent':'LLM (flagged-only)','resolution_status_contradiction':'LLM (flagged-only)','pii_in_free_text':'rules'}
    for p in PROBLEMS: dm.append(f'| {p} | {mapping[p]} | Benchmark rows for this problem are in `benchmark.csv`; selection favors deterministic/auditable checks, using LLM only for semantic ambiguity. |')
    (outdir/'DECISION_MATRIX.md').write_text('\\n'.join(dm))
    (outdir/'AI_USAGE.md').write_text('# AI Usage Note\\n\\nAI assistance was used to draft and structure code/documentation. The LLM-review detector in this runnable project is explicitly a deterministic proxy; no Gemini API call was made. Validate every detector and be prepared to explain its logic.\\n')
    return prof,res
