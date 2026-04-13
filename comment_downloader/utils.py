import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time

def fetch_url_title(url):
    """
    URL에서 제목을 가져오는 함수
    
    Args:
        url (str): 확인할 URL
        
    Returns:
        str: URL의 제목, 실패 시 None
    """
    try:
        # URL 유효성 검사
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return None
            
        # HTTP 요청
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 타임아웃 설정 (5초)
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        # HTML 파싱
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 제목 태그에서 텍스트 추출
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        else:
            # meta 태그에서 제목 가져오기
            meta_title = soup.find('meta', attrs={'name': 'title'})
            if meta_title:
                return meta_title.get('content', '').strip()
            else:
                return "제목 없음"
                
    except Exception as e:
        # 오류 발생 시 None 반환
        return None