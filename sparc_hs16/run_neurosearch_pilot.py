from __future__ import annotations

import json

from sparc_hs16.neurosearch import successive_halving_search


def main() -> None:
    report = successive_halving_search()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
