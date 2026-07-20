from minimal_predictive_lm.active_language_intervention import BASE, Episode, PartitionSemanticInducer, UNSEEN, evaluate, make_train


def test_seen_forms_can_be_bound_by_partition_effect():
    model=PartitionSemanticInducer(); model.fit(make_train(4,1)); seen,_=evaluate(model); assert seen==1.0


def test_unseen_paraphrases_are_not_falsely_claimed_as_understood():
    model=PartitionSemanticInducer(); model.fit(make_train(64,7)); _,unseen=evaluate(model); assert unseen==0.0


def test_imposed_effect_accepts_semantically_unrelated_decoy():
    model=PartitionSemanticInducer(); model.fit([Episode('d','今日の天気は',BASE['color'][0][1])]); assert model.infer_signature('今日の天気は') is not None


def test_capacity_is_bounded_on_controlled_scale():
    model=PartitionSemanticInducer(); model.fit(make_train(64,19)); assert model.bytes()<10_000
