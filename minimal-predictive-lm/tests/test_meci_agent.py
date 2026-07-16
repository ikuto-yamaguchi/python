from minimal_predictive_lm.meci_agent import MECICognitiveAgent
from minimal_predictive_lm.meci_chat import DialogueRecord


def test_online_fact_learning_and_recall() -> None:
    agent = MECICognitiveAgent()
    assert agent.reply("私の名前は郁斗です。").mechanism == "online-semantic-learning"
    assert agent.reply("こんにちは").text.startswith("こんにちは")
    assert agent.reply("私の名前は何？").text == "ユーザーの名前は郁斗です。"


def test_three_hop_inference() -> None:
    agent = MECICognitiveAgent()
    agent.reply("アキラは高校生です。")
    agent.reply("高校生は学生です。")
    agent.reply("学生は人です。")
    reply = agent.reply("アキラは人？")
    assert reply.mechanism == "transitive-reasoning"
    assert reply.text.startswith("はい。")
    assert len(reply.supporting_facts) == 3


def test_property_cause_arithmetic_and_unknown() -> None:
    agent = MECICognitiveAgent()
    agent.reply("富士山の高さは3776メートルです。")
    assert agent.reply("富士山の高さは何？").text == "富士山の高さは3776メートルです。"
    agent.reply("道路が濡れているのは雨が降ったからです。")
    assert agent.reply("道路が濡れているのはなぜ？").text == "雨が降ったからです。"
    assert agent.reply("18*7-9は？").text == "117です。"
    unknown = agent.reply("未解決の統一理論を完成させて")
    assert unknown.mechanism == "calibrated-unknown"


def test_sparse_episode_paraphrase_and_roundtrip() -> None:
    agent = MECICognitiveAgent().fit(
        [DialogueRecord("調子はどう？", "順調です。今日は何を考えますか？")]
    )
    assert agent.reply("調子どう？").text == "順調です。今日は何を考えますか？"
    agent.reply("私の名前は郁斗です。")
    restored = MECICognitiveAgent.from_bytes(agent.to_bytes())
    assert restored.reply("私の名前は何？").text == "ユーザーの名前は郁斗です。"
