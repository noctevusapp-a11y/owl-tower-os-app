#!/bin/bash
# Python vs SQL spec_key normalisation (needs PGHOST etc. and a database with the costdb schema, e.g. f3syn / f3_repro)
DB=${1:-f3_repro}
PYTHONPATH=/home/user/owl-tower-os-app/cost-db/pipeline python3 -B - <<PY
import json, subprocess
from costdb.ids import norm_attr_value as n
for v in [" 5.50", "5.50 ", "a b", "İ", "0.50", "5_8", "NaN", "1e3"]:
    sql = "select costdb.norm_attr(%s::jsonb)" % ("'" + json.dumps(v) + "'")
    out = subprocess.run(['psql','-At','-d','$DB','-c',sql],capture_output=True,text=True).stdout.strip()
    print(repr(v), 'py=', repr(n(v)), 'sql=', repr(out), 'SAME' if n(v)==out else 'DIFF')
PY
