import os
import sys
import uuid
import datetime
import json
import logging

import httpx
import dotenv

#get api information
dotenv.load_dotenv()
GOOGLE_SEARCH_URL=os.getenv('GOOGLE_SEARCH_URL')
GOOGLE_SEARCH_API_KEY=os.getenv('GOOGLE_SEARCH_API_KEY')
GOOGLE_SEARCH_CX=os.getenv('GOOGLE_SEARCH_CX')
EXPORT_COMMENT_URL=os.getenv('EXPORT_COMMENT_URL')
EXPORT_COMMENT_API_KEY=os.getenv('EXPORT_COMMENT_API_KEY')

#logger
logger=logging.getLogger(__name__)

#platform url
platform_urls = {
    "BestBuy": "www.bestbuy.com",
    "Youtube": "www.youtube.com",
    "Walmart": "www.walmart.com",
    #"Amazon": "www.amazon.com",
    "Reddit": "www.reddit.com"
}

def google_search(query: str, googleSearchId: str, site: str, max_search_num: int = 100):
    try:
        # Convert platform name to URL if needed
        if site in platform_urls:
            site = platform_urls[site]
        with httpx.Client() as client:
            if site == 'www.bestbuy.com':
                query = query.replace('intitle', 'inurl')
            if site == 'www.youtube.com':
                query = query.replace('intitle', 'intext')
            start = 1
            next_page_exists = True
            total_results = list()
            while start < max_search_num and next_page_exists:
                logger.debug(f"Starting google search with startnum {start}...")
                url = f"{GOOGLE_SEARCH_URL}"
                params = {
                    "q": query,
                    "key": GOOGLE_SEARCH_API_KEY,
                    "cx": GOOGLE_SEARCH_CX,
                    "num": 10,
                    "start": start,
                    "siteSearch": site
                }
                print(params)
                search_result = client.get(url, params=params)
                print(search_result.url)
                if search_result.status_code != 200:
                    raise Exception(f"Google Search API Returns {search_result.status_code}: f{search_result.content}")
                if search_result.json().get('items', None) != None: 
                    # with open(f"download_result/google_search_result/{googleSearchId}_{start}.json", "w") as f:
                    #     logger.debug(f"Saving google search result {googleSearchId}_{start}...")
                    #     f.write(json.dumps(search_result.json()))
                    total_results.extend(search_result.json()['items'])
                    print(search_result.json())
                else:
                    print(search_result.json())

                if search_result.json()['queries'].get('nextPage', False):
                    start += 10
                else:
                    next_page_exists = False

    except Exception as err:
        raise Exception(err)
    
    logger.info(f"Getting google_search_result: {len(total_results)}")
    return total_results

if __name__ == "__main__":
    query = sys.argv[1]
    #query = "LG TV OLED"
    sites = list(platform_urls.values())
    for site in sites:
        googleSearchId = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{datetime.datetime.now()}_{site}_{query}"))
        google_search(query, googleSearchId, site, 5)