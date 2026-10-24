#!/bin/bash
# F3-32: second build after the first promotion crashes. Works on a throw-away copy, never on the repository.
R=/home/user/owl-tower-os-app/cost-db
D=/tmp/claude-0/f3/copy_build_twice
rm -rf $D && mkdir -p $D && cp -r $R/. $D/ && rm -rf $D/.git
cd $D
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import sys
sys.path[:0] = ['pipeline', '.']
from pathlib import Path
from tests.fixtures import synthetic as S
from costdb.store import Database
db = Database.load_csv_dir()
SRC = 'SRC-FETCHTEST'
S.add_source(db, SRC, method='fetched_primary', review='unreviewed', reuse='open_license')
for s in db['sources']:
    if s['source_id'] == SRC: s.update(reviewed_by=None, reviewed_at=None)
S.add_product(db, 'PRD-TESTPOP1', 'gyp_half_reg_4x8', 32, 'SF', 'TB', 'TB-1', source=SRC)
S.add_obs(db, 'OBS-TESTPOP1', 'PRD-TESTPOP1', '12.80', 32, 'SF', source=SRC, channel='public_price_list')
for t, k, i in (('products', 'product_id', 'PRD-TESTPOP1'), ('price_observations', 'observation_id', 'OBS-TESTPOP1')):
    for r in db[t]:
        if r[k] == i: r.update(review_status='unreviewed', reviewed_by=None, reviewed_at=None)
db.write_csv_dir(Path('data/csv'))
PY
echo "--- build #1"; PYTHONDONTWRITEBYTECODE=1 python3 -B pipeline/scripts/build.py --skip-tests 2>&1 | tail -3; echo "exit ${PIPESTATUS[0]}"
echo "--- build #2"; PYTHONDONTWRITEBYTECODE=1 python3 -B pipeline/scripts/build.py --skip-tests 2>&1 | tail -3; echo "exit ${PIPESTATUS[0]}"
