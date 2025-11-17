"""
Entrypoint to run scraping + processing + storage + analysis.
Simple CLI: python -m src.main
"""
import argparse
import yaml
import os
from src.scraper import TweetScraper
from src.processor import records_to_dataframe, deduplicate, reservoir_sample
from src.storage import save_parquet, load_parquet
from src.analysis import compute_tfidf, compute_embeddings, aggregate_signals
from src.logger import logger
from datetime import datetime

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def merge_and_store(df, path):
    # load existing
    existing = None
    try:
        existing = load_parquet(path)
    except Exception:
        existing = None
    if existing is None:
        out = df
    else:
        out = pd.concat([existing, df], ignore_index=True)
        out = out.drop_duplicates(subset=["tweet_id"])
    save_parquet(out, path)

def run_scrape_loop(cfg):
    scraper = TweetScraper(headless=cfg['scrape'].get('headless', True))
    collected = []
    try:
        for kw in cfg['keywords']:
            logger.info(f"Scraping keyword: {kw}")
            data = scraper.scrape_hashtag(kw, max_items=cfg['scrape']['max_tweets'], max_scrolls=cfg['scrape']['max_scrolls'], min_recent_hours=cfg['scrape']['min_recent_hours'])
            collected.extend(data)
            # polite pause between keywords
            from src.utils import rand_sleep
            rand_sleep(cfg['scrape'].get('window_seconds', 2.0), 1.0)
    finally:
        scraper.close()
    logger.info(f"Total collected raw records: {len(collected)}")
    df = records_to_dataframe(collected)
    df = deduplicate(df, key="tweet_id")
    # store
    out_path = cfg['storage']['parquet_file']
    save_parquet(df, out_path)
    return df

def run_analysis(cfg, df):
    # sample if needed
    from src.processor import reservoir_sample
    sample_limit = cfg['processing'].get('sample_limit', 50000)
    if len(df) > sample_limit:
        df_sample = reservoir_sample(df, k=sample_limit)
    else:
        df_sample = df
    X, vect = compute_tfidf(df_sample['content'].astype(str), max_features=cfg['analysis']['tfidf_max_features'], ngram_range=tuple(cfg['analysis']['tfidf_ngram_range']))
    signals = aggregate_signals(X, vect, df_sample, top_k=cfg['analysis']['top_k_terms'])
    # attach timestamp and store signals
    signals['generated_at'] = datetime.utcnow().isoformat()
    save_parquet(signals, cfg['storage']['output_dir'] + "/signals.parquet")
    logger.info("Analysis complete")
    return signals

if _name_ == "_main_":
    import pandas as pd
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--mode", choices=["scrape", "analysis", "both"], default="both")
    args = parser.parse_args()
    cfg = load_config(args.config)
    if args.mode in ("scrape", "both"):
        df = run_scrape_loop(cfg)
    else:
        df = pd.read_parquet(cfg['storage']['parquet_file'])
    if args.mode in ("analysis", "both"):
        run_analysis(cfg, df)
