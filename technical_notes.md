Technical notes — Market-Intel

1) Architecture
- Scraper: Selenium (undetected-chromedriver) -> fetch live search pages by hashtag -> parse article elements -> extract content and timestamp -> store JSON-like records.
- Processor: convert to DataFrame, deduplicate by tweet_id, normalize text.
- Storage: Parquet files stored under outputs/; Parquet chosen for compact, columnar storage and easy query via pandas/pyarrow.
- Analysis: TF-IDF vectorization + optional SBERT embeddings; TF-IDF used for fast, memory-efficient signals.

2) Anti-bot & reliability
- Randomized sleeps, jitter, occasional longer delays.
- Rotate queries across multiple hashtags.
- Optional proxy rotation (supply --proxy or update config).
- Use undetected-chromedriver to reduce simple automation detection; still not bulletproof.

3) Rate-limiting & politeness
- Keep scrolls and page requests modest: max_scrolls and batch_sleep_sec in config.
- Use min_recent_hours to ignore old content and avoid unnecessary scrolls.

4) Scaling to 10x data
- Move scraping to a distributed worker pool (k8s pods), each assigned a subset of keywords or geographic queries.
- Use Kafka/Cloud PubSub to stream raw JSON, consumers for processing and storing to Parquet/BigQuery.
- Replace TF-IDF with hashed or incremental vectorizers to handle extremely large vocabularies.
- For storage, use partitioned Parquet by date and write-leveling to cloud storage (GCS / S3).

5) Memory-efficient visualization strategies
- Reservoir sampling for large corpus.
- Streaming plots: only keep summaries (e.g., hourly aggregates) and plot these aggregates.
- Use downsampled embeddings for 2D plots (UMAP) and incremental visualization.

6) Legal and ethical
- Scraping public pages must follow site rules. Using a third-party API (official) is safer when available.
