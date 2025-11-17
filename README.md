# Market-Intel (Twitter/X) — Real-time market intelligence for Indian stocks

This repository is a production-minded Python system to collect and analyze public tweets related to Indian stock market hashtags (#nifty50, #sensex, #intraday, #banknifty) without using any paid API.

*Core capabilities*
- Scrape X.com search pages for given hashtags (Selenium-based).
- Collect: tweet_id, username, timestamp, content, mentions, hashtags, url.
- Deduplicate and store as Parquet.
- Convert text -> TF-IDF signals; optional sentence embeddings.
- Memory-efficient sampling / reservoir sampling for large data.
- Basic anti-bot defense: randomized sleeps, headless config, undetected-chromedriver.
- Signal aggregation with confidence scores; saved as Parquet.

*Quickstart*
1. Install Chrome and matching chromedriver. On Linux:
   - Install Chrome stable.
   - Optionally install chromedriver or rely on undetected-chromedriver (recommended).
2. Create a virtualenv and install requirements:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
3. Configure config.yaml (output paths, keywords, max items).
4. Run: