from __future__ import annotations

from . import close_communication_experiment as experiment
from .close_communication_parquet import load_jaquad_parquet
from .close_mambapy_runtime import MambaPySanRuntime


def main() -> None:
    experiment.MambaSanRuntime = MambaPySanRuntime
    experiment.load_jaquad = load_jaquad_parquet
    experiment.main()


if __name__ == "__main__":
    main()
