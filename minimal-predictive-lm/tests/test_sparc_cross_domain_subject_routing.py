from minimal_predictive_lm.sparc_cross_domain_plans_v2 import SPARCHS11ModelV2
from minimal_predictive_lm.sparc_role_induction_v3 import SPARCHS10ModelV3


def test_query_local_subject_routing_survives_large_shared_prefix_bank() -> None:
    model = SPARCHS11ModelV2(SPARCHS10ModelV3())
    for index in range(2000):
        subject = f"輸送体A{index:04d}"
        model.ingest_fact(
            f"{subject}の速度は時速{40 + index % 20}kmである。",
            source_id=f"速度{index}",
        )
        model.ingest_fact(
            f"{subject}の運転時間は2時間である。",
            source_id=f"時間{index}",
        )
    examples = []
    for index in (3, 117, 902):
        subject = f"輸送体A{index:04d}"
        examples.append(
            (
                f"{subject}の移動距離は何kmですか？",
                f"{(40 + index % 20) * 2}km",
            )
        )
    model.teach_plan(examples)
    reply = model.reply("輸送体A1999の移動距離は何kmですか？")
    assert reply.text.startswith(f"{(40 + 1999 % 20) * 2}kmです")
    assert model.plans.last_subject_substring_checks <= 32
    assert model.plans.report()["global_subject_scan_used"] is False
