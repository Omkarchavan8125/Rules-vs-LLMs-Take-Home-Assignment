from src.tax_engine import calculate

def test_nonnegative_and_regime_output():
    r=calculate({'salary':1000000})
    assert r['old']['total_tax']>=0 and r['new']['total_tax']>=0
    assert r['recommendation'] in ('old','new')

def test_zero_salary():
    r=calculate({'salary':0})
    assert r['old']['total_tax']==0 and r['new']['total_tax']==0
