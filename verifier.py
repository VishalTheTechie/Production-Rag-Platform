"""Stage-2 check for the cache: a cross-encoder trained to spot duplicate questions.
It reads both questions TOGETHER, so it notices small changes that embeddings miss."""
import config

_model = None


def _get():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder
        _model = CrossEncoder(config.VERIFY_MODEL)   # downloads once, runs on your CPU
    return _model


def same_question_scores(pairs):
    """pairs = [(question_a, question_b), ...] -> list of scores from 0 to 1."""
    return [float(s) for s in _get().predict(pairs)]


def same_question_score(a, b):
    return same_question_scores([(a, b)])[0]
