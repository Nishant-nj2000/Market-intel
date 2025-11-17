import pandas as pd
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from src.logger import logger
import os

def save_parquet(df: pd.DataFrame, path: str, mode: str = "overwrite"):
    Path(os.path.dirname(path) or ".").mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving {len(df)} rows to parquet: {path}")
    df.to_parquet(path, index=False)

def load_parquet(path: str):
    if not Path(path).exists():
        return None
    return pd.read_parquet(path)