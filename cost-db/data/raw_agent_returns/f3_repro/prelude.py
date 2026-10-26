# run from anywhere:  PYTHONDONTWRITEBYTECODE=1 python3 -B <file>
import sys
R = '/home/user/owl-tower-os-app/cost-db'
sys.path[:0] = [R, R + '/pipeline']
from datetime import date
from decimal import Decimal as D
from tests.fixtures import synthetic as S
from costdb.calc import Engine, RunParams
from costdb.validate import validate, promote_validated
WI = S.WI
def run(db, **kw): return Engine(db).unit_cost(WI, 1, S.params(**kw))
def mat(r): return [l for l in r.lines if l['line_kind'] == 'material'][0]
def codes(r): return [(m['code'], m['component_ref']) for m in r.run['missing_inputs']]
