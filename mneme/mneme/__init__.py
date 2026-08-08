"""MNEME: Memory-Native Efficient Model.

トークナイザーフリー(バイトレベル + エントロピー動的パッチング)で、
知識をパラメータではなく外部の完全記憶(エピソード記憶)に置く
特化型知能アーキテクチャのプロトタイプ。
"""

from .memory import EpisodicMemory
from .patcher import EntropyPatcher
from .modules import ByteEncoder, ByteDecoder, PAD, BOS, EOS, VOCAB
from .recall import MemoryRecallModel, ParametricRecallModel, make_facts
from .lm import MnemeLM

__all__ = [
    "EpisodicMemory",
    "EntropyPatcher",
    "ByteEncoder",
    "ByteDecoder",
    "MemoryRecallModel",
    "ParametricRecallModel",
    "make_facts",
    "MnemeLM",
    "PAD",
    "BOS",
    "EOS",
    "VOCAB",
]
