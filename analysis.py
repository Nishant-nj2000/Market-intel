"""
Text -> Signal conversion: TF-IDF vectors, optional embeddings, signal aggregation.
Memory-efficient plotting helpers included.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import pandas as pd
from src.logger import logger
from typing import Tuple, Optional
from sentence_transformers import SentenceTransformer

def compute_tfidf(documents: pd.Series, max_features=20000, ngram_range=(1,2)):
    logger.info("Fitting TF-IDF")
    vect = TfidfVectorizer(max_features=max_features, ngram_range=ngram_range, stop_words='english')
    X = vect.fit_transform(documents.fillna("").astype(str))
    logger.info(f"TF-IDF mapped {X.shape[0]} docs to {X.shape[1]} features")
    return X, vect

def compute_embeddings(documents: pd.Series, model_name: str = "all-MiniLM-L6-v2", batch_size: int = 64):
    logger.info(f"Loading embedding model {model_name} (may be slow on first run)")
    model = SentenceTransformer(model_name)
    emb = model.encode(documents.fillna("").astype(str).tolist(), batch_size=batch_size, show_progress_bar=True)
    return np.array(emb)

def aggregate_signals(tfidf_matrix, vectorizer, df, top_k=50):
    """
    Produce a lightweight composite signal:
      - for each doc, compute sum of TF-IDF weights for a curated top-k terms
      - produce normalized score and confidence (based on doc length and tfidf density)
    """
    feature_names = np.array(vectorizer.get_feature_names_out())
    # pick global top-k features by mean idf-weight across corpus
    col_means = np.asarray(tfidf_matrix.mean(axis=0)).ravel()
    top_idx = np.argsort(col_means)[-top_k:]
    selected = tfidf_matrix[:, top_idx]
    scores = np.asarray(selected.sum(axis=1)).ravel()
    # normalize
    scores_norm = (scores - scores.min()) / (scores.max() - scores.min() + 1e-9)
    confidence = []
    lengths = df['content'].fillna("").str.split().str.len().fillna(0).values
    # confidence heuristic: longer tweets and denser tfidf => higher confidence
    density = (scores / (lengths + 1e-6))
    density_norm = (density - density.min()) / (density.max() - density.min() + 1e-9)
    confidence = 0.6 * density_norm + 0.4 * (lengths / (lengths.max() + 1e-9))
    return pd.DataFrame({
        "tweet_id": df['tweet_id'].values,
        "score": scores_norm,
        "confidence": confidence
    })

# memory-efficient plotting: incremental/reservoir-based (see docs)
