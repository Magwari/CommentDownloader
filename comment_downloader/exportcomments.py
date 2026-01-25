import os
import sys
import time
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

logger=logging.getLogger(__name__)

API_BASE = f"{EXPORT_COMMENT_URL}/job"
API_KEY = "YOUR_API_KEY"  # 필요시 인증키
# OUTPUT_DIR = os.path.join("download_reault", "exportcomments_result")
# os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_exportcomments_task(url):
    print(f"Creating exportcomments job of {url}...", flush=True)
    tries = 0
    while tries < 5:
        with httpx.Client(verify=False) as client:
            export_url = f"{EXPORT_COMMENT_URL}/job"
            headers = {
                "X-AUTH-TOKEN": EXPORT_COMMENT_API_KEY,
                "Content-Type": "application/json"
            }
            data = {
                "url": url
            }
            request = client.post(export_url, headers=headers, json=data)
            if request.status_code == 429:
                request.json()
                print("API throttled. wait 3 minuits...", flush=True)
                time.sleep(180)
                tries += 1
                continue

            if request.status_code != 201:
                raise Exception(f"ExportComment API Returns {request.status_code}: f{request.content}")
            
            guid = request.json().get("guid")
            print(f"Created Job {guid}", flush=True)
            if not guid:
                print(f"No GUID for {url}, response: {request.content}", flush=True)
                raise Exception(f"ExportComment API Not Returns guid.")

            # 2. 폴링으로 상태 확인
            while True:
                status = check_export(guid)
                print("Current Status: ", status.get("status"), flush=True)
                if status.get("status") == "done":
                    return status
                time.sleep(10)
            
def check_export(guid: str):
    headers = {"Content-Type": "application/json"}
    headers = {
        "X-AUTH-TOKEN": EXPORT_COMMENT_API_KEY,
        "Content-Type": "application/json"
    }
    url = f"{API_BASE}/{guid}"
    resp = httpx.get(url, headers=headers, verify=False)
    resp.raise_for_status()
    return resp.json()

def download_json(json_url: str):
    resp = httpx.get(json_url, verify=False)
    resp.raise_for_status()
    return resp.json()

def process_url(url,options=None):
    # 1. export 생성
    res = create_exportcomments_task(url)
    guid = res.get("guid") or res.get("id")
    json_url = res.get("json_url")
    json_data = download_json(json_url)
    return guid, json_data

if __name__ == "__main__":
    url_file = sys.argv[1]
    url_list = set()
    with open(url_file) as f:
        data = json.loads(f.read())
        for item in data['items']:
            url_list.add(item['link'])
    url_list = list(url_list)

    for url in list(url_list):
        try:
            guid, json_data = process_url(url)
            with open(f'download_result/exportcomments_result/{guid}.json', 'w', encoding='utf-8') as f:
                f.write(json.dumps(json_data, ensure_ascii=False))
        except:
            print(f"error with {url}", flush=True)