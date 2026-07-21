import random
from reversible_episodic_binding import ReversibleEpisodicBinder, make_episode

def test_renamed_retrieval():
    rng=random.Random(1)
    train=[make_episode(rng,'memory',False,4)[0] for _ in range(64)]
    m=ReversibleEpisodicBinder();m.fit(train)
    seq,ans=make_episode(random.Random(9),'memory',True,5)
    pos=seq.index('回答')
    pred,_,_=m.bind_predict(seq[:pos+1])
    assert pred==ans

def test_unseen_value_is_not_fabricated():
    rng=random.Random(1)
    train=[make_episode(rng,'memory',False,4)[0] for _ in range(64)]
    m=ReversibleEpisodicBinder();m.fit(train)
    seq,ans=make_episode(random.Random(9),'memory',True,5,True)
    pos=seq.index('回答')
    pred,_,_=m.bind_predict(seq[:pos+1])
    assert pred!=ans

def test_decoy_transform_not_claimed():
    rng=random.Random(2)
    train=[make_episode(rng,'memory',False,4)[0] for _ in range(64)]
    m=ReversibleEpisodicBinder();m.fit(train)
    seq,ans=make_episode(random.Random(10),'decoy',True,1)
    pos=seq.index('回答')
    pred,_,_=m.bind_predict(seq[:pos+1])
    assert pred!=ans
