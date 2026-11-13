from sentence_transformers import SentenceTransformer
import config

_model = SentenceTransformer(config.EMBED_MODEL)  # downloads once, runs locally


def embed(texts):
    return _model.encode(texts, normalize_embeddings=True).tolist()


def embed_one(text):
    return embed([text])[0]
