import time
import random
import requests

NBA_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Connection": "keep-alive",
}

def nba_get(url: str, params: dict, timeout=30, max_retries=3):
    """
    Safe NBA Stats GET request.
    - Browser headers
    - Retry on timeout
    - Mandatory sleep to avoid bans
    """

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                url,
                headers=NBA_HEADERS,
                params=params,
                timeout=timeout,
            )
            response.raise_for_status()

            # NBA Stats returns JSON as text/plain sometimes
            return response.json()

        except Exception as e:
            print(f"[WARN] NBA request failed (attempt {attempt}): {e}")

            # Backoff: wait longer each retry
            sleep_time = 2 + attempt + random.uniform(0.5, 1.5)
            time.sleep(sleep_time)

    print("[ERROR] NBA request failed permanently.")
    return None
