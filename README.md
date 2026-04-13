# CommentDownloader

온라인 소비자 리뷰를 검색하고 수집하는 데 사용되는 PyQt 기반 GUI 애플리케이션입니다.

## 기능

- 다양한 플랫폼(예: BestBuy, Walmart, Youtube, Reddit)에서 제품 리뷰 검색
- 제품 스펙(브랜드, 제품군, 패널타입, 해상도 등)을 기반으로 정밀 검색
- 검색된 URL에서 댓글 데이터 수집
- 수집된 데이터를 JSON 파일로 저장

## 설치 방법

### 1. Git에서 코드 다운로드

```bash
git clone https://github.com/Magwari/CommentDownloader
cd CommentDownloader
```

### 2. 의존성 설치

```bash
pip install .
```

## 실행 방법(아래 중 하나를 선택)

### 1. GUI 애플리케이션 실행

```bash
python main.py
```

### 2. EXE 파일 생성

```bash
pyinstaller --onefile --windowed --name CommentDownloader main.py
```

생성된 EXE 파일은 `dist` 폴더에 위치합니다.

EXE 파일과 같은 위치에 `.env` 파일을 복사해야 합니다.  
`.env` 파일은 애플리케이션 실행 시 필요한 API 키 및 설정 정보를 포함합니다.

예시 `.env` 파일 내용:
```
GOOGLE_SEARCH_URL=https://www.googleapis.com/customsearch/v1
GOOGLE_SEARCH_API_KEY=your_google_api_key
GOOGLE_SEARCH_CX=your_custom_search_engine_id
EXPORT_COMMENT_URL=https://your-export-api.com
EXPORT_COMMENT_API_KEY=your_export_api_key
```


## 프로젝트 구조

```
CommentDownloader/
├── main.py                 # 메인 GUI 애플리케이션
├── pyproject.toml          # 패키지 및 의존성 정의
├── .gitignore              # Git 무시 파일
├── comment_downloader/
│   ├── __init__.py
│   ├── google_search.py    # Google 검색 기능
│   ├── exportcomments.py   # 댓글 수집 기능
│   └── .env                # 환경 변수 파일
```

## 개발 환경 요구사항

- Python 3.8 이상
- PySide6
- httpx
- python-dotenv

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.