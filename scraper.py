"""
Selenium-based scraper that scrolls X.com search pages for specified hashtags
and extracts tweet data without using any private API.

NOTE: scraping can break due to front-end changes. Keep selectors up-to-date.
"""
import time
import re
from datetime import datetime
from typing import Dict, List
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from src.utils import rand_sleep, clean_text, parse_hashtags, parse_mentions, within_last_hours
from src.logger import logger
import random

TWITTER_SEARCH_URL = "https://x.com/search?q={query}&f=live"

class TweetScraper:
    def _init_(self, headless=True, proxy: str = None):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--lang=en-US")
        if proxy:
            chrome_options.add_argument(f"--proxy-server={proxy}")
        # reduce fingerprint
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.driver = uc.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(60)
        logger.info("WebDriver started")

    def _open_search(self, query: str):
        url = TWITTER_SEARCH_URL.format(query=query)
        logger.info(f"Opening search: {url}")
        self.driver.get(url)
        rand_sleep(1.5, 1.0)

    def _scroll_and_collect(self, max_scrolls=200, max_items=2000, min_recent_hours=24):
        collected = []
        seen_ids = set()
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scrolls = 0
        while scrolls < max_scrolls and len(collected) < max_items:
            cards = self.driver.find_elements(By.XPATH, "//article")
            logger.debug(f"Found {len(cards)} article elements")
            for a in cards:
                try:
                    tid = a.get_attribute("data-testid") or ""
                    # try to extract tweet id from href inside
                    anchors = a.find_elements(By.TAG_NAME, "a")
                    tweet_url = None
                    for anc in anchors:
                        href = anc.get_attribute("href") or ""
                        if "/status/" in href:
                            tweet_url = href
                            break
                    tweet_id = None
                    if tweet_url:
                        tweet_id = tweet_url.split("/")[-1]
                    if not tweet_id:
                        continue
                    if tweet_id in seen_ids:
                        continue

                    username = ""
                    try:
                        user_el = a.find_element(By.XPATH, ".//div[@dir='ltr']//span")
                        username = user_el.text
                    except:
                        username = ""

                    content = ""
                    try:
                        # tweet text is often inside div[@data-testid='tweetText']
                        content_el = a.find_element(By.XPATH, ".//div[@data-testid='tweetText']")
                        content = content_el.text
                    except:
                        try:
                            content = a.text
                        except:
                            content = ""

                    # timestamp
                    ts = None
                    try:
                        time_el = a.find_element(By.XPATH, ".//time")
                        ts_str = time_el.get_attribute("datetime")
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except Exception:
                        ts = None

                    # engagement
                    engagement = {"reply": 0, "retweet": 0, "like": 0}
                    try:
                        stats = a.find_elements(By.XPATH, ".//div[@data-testid]/div/span")
                        # fallback: parse spans with numbers
                        for s in stats:
                            txt = s.text.strip()
                            if txt:
                                # crude parsing; improve as site changes
                                pass
                    except:
                        pass

                    # build record
                    record = {
                        "tweet_id": tweet_id,
                        "username": username,
                        "timestamp": ts.isoformat() if ts else None,
                        "content": clean_text(content),
                        "hashtags": parse_hashtags(content),
                        "mentions": parse_mentions(content),
                        "raw_engagement": None,
                        "scraped_at": datetime.utcnow().isoformat(),
                        "tweet_url": tweet_url,
                    }

                    if ts and not within_last_hours(ts, min_recent_hours):
                        # skip older tweets
                        continue

                    collected.append(record)
                    seen_ids.add(tweet_id)
                    if len(collected) >= max_items:
                        break
                except Exception as e:
                    logger.debug("card parse error", exc_info=e)
                    continue

            # scroll
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            rand_sleep(0.8, 1.0)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # small chance more content loads with a little wait
                rand_sleep(2, 1)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    logger.info("Reached page bottom or no further content.")
                    break
            last_height = new_height
            scrolls += 1
            # occasionally randomize to look less bot-like
            if random.random() < 0.05:
                rand_sleep(3, 2)

        return collected

    def close(self):
        try:
            self.driver.quit()
        except:
            pass

    def scrape_hashtag(self, query: str, max_items=1000, max_scrolls=200, min_recent_hours=24):
        try:
            self._open_search(query)
            data = self._scroll_and_collect(max_scrolls=max_scrolls, max_items=max_items, min_recent_hours=min_recent_hours)
            return data
        except Exception as e:
            logger.exception("Scrape failed", exc_info=e)
            return []
