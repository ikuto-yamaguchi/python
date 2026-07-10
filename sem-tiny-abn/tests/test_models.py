import torch

from sem_tiny_abn.losses import compute_loss
from sem_tiny_abn.models import build_model


def test_all_models_forward_batch_one():
    torch.set_num_threads(1)
    x = torch.randn(1, 4, 128, 128)
    for name in ("tiny_cnn", "tiny_abn", "tiny_freq_abn"):
        model = build_model(name, 4, 2, width=0.75, depth=1, norm="group", block_type="standard")
        output = model(x)
        assert output["logits"].shape == (1, 2)
        if name != "tiny_cnn":
            assert output["attention"].shape == (1, 1, 16, 16)
            assert torch.all(output["attention"] >= 0)
            assert torch.all(output["attention"] <= 1)


def test_abn_attention_and_auxiliary_paths_receive_gradients():
    torch.set_num_threads(1)
    model = build_model("tiny_abn", 4, 2, width=0.75, depth=1, norm="group")
    output = model(torch.randn(2, 4, 96, 96))
    loss, _ = compute_loss(output, torch.tensor([0, 1]), task="multiclass", aux_weight=1.0)
    loss.backward()
    assert model.attention_branch.class_maps.weight.grad is not None
    assert model.attention_branch.attention_from_classes.weight.grad is not None
    assert model.features.tail[0][0].conv1[0].weight.grad is not None


def test_group_norm_allows_batch_size_one_train_step():
    model = build_model("tiny_abn", 4, 2, width=0.75, norm="group")
    output = model(torch.randn(1, 4, 64, 64))
    loss, _ = compute_loss(output, torch.tensor([1]), task="multiclass")
    loss.backward()
    assert torch.isfinite(loss)
