"""
Data cleaning, deduplication, sampling, and lightweight streaming helpers.
"""
import pandas as pd
from typing import List
from src.logger import logger
from collections import deque
from src.utils import clean_text
import numpy as np

def records_to_dataframe(records: List[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    # normalize columns
    df['content'] = df.get('content', '').fillna('').apply(clean_text)
    # convert timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
    return df

def deduplicate(df: pd.DataFrame, key: str = "tweet_id") -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=[key])
    after = len(df)
    logger.info(f"Deduplicated: {before} -> {after}")
    return df

def reservoir_sample(df: pd.DataFrame, k: int = 10000, seed: int = 42) -> pd.DataFrame:
    if len(df) <= k:
        return df
    np.random.seed(seed)
    idx = np.random.choice(df.index, size=k, replace=False)
    return df.loc[idx].reset_index(drop=True)
