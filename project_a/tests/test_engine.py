from src.tax_engine import calculate
def test_zero(): assert calculate({'salary':0})['old']['total_tax']==0
def test_output(): assert calculate({'salary':1000000})['recommended_regime'] in ['old','new']
