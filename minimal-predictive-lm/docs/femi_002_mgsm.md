# FEMI-002 public MGSM gate

FEMI-002 evaluates one non-neural executable learner on the public Japanese MGSM corpus.

The learner extracts number spans, searches arithmetic expressions, selects reusable programs by description length and cross-example support, and indexes them with character n-grams. It receives no task IDs or manually assigned operation labels.

Two scores are kept separate:

- eight published Japanese exemplars to all 250 questions;
- first 200 labelled public questions to a final 50-question holdout.

The 200/50 result is a public adaptation split, not the official zero-shot MGSM score.

The experiment reports exact accuracy, coverage, synthesis expansions, serialized model bytes, peak Python memory, attempted programs per question, and throughput.

The frozen gate requires at least 10% exact accuracy on the final 50 questions and executable solutions for at least 80 of the 200 training questions. Failure rejects the current learner.

A pass is still not Japanese high-school-level intelligence, conversational competence, an established novelty claim, or proof of superiority over a matched language model. Later gates must add public Japanese reading, science, social studies, and high-school mathematics while measuring dependency width and all resource costs.
