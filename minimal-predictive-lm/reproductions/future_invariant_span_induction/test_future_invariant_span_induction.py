from future_invariant_span_induction import Inducer, make_dialogues, overlap_f1

def test_deterministic_induction():
    pairs,_=make_dialogues(1,32)
    a=Inducer('future_invariant').fit(pairs)
    b=Inducer('future_invariant').fit(pairs)
    assert a.scores==b.scores

def test_no_unseen_surface_cheat():
    pairs,_=make_dialogues(1,64)
    m=Inducer('future_invariant').fit(pairs)
    u='私は未知語999に住んでいます。'
    p=m.predict_span(u)
    assert p is None or p[3] != '未知語999'

def test_overlap_metric():
    assert overlap_f1((1.0,2,4,'ab'),(2,4,'ab',0))==1.0
