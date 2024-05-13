
# Crews_ML

이 프로젝트는 가천대학교 소프트웨어학과의 졸업작품으로, DCInside와 Naver News에서 데이터를 크롤링한 후 감정 분석을 수행하고 MongoDB에 결과를 저장합니다.

This project is a graduation work of the School of Software at Gachon University. It crawls data from DCInside and Naver News, performs sentiment analysis, and stores the results in MongoDB.

## 구성 요소 / Components

### Crawler
- **dc-pipe.py & news-pipe.py**
  - **기능**: DCInside 및 Naver News에서 데이터를 크롤링. 데이터에 대한 감정 분석을 수행하고 결과를 MongoDB에 저장합니다.
  - **Features**: Crawls data from DCInside and Naver News. Performs sentiment analysis on the data and stores the results in MongoDB.
  - **AI 모델 / AI Models**:
    - **감정 분석 / Sentiment Analysis**: Transformer 기반의 모델을 사용하여 텍스트의 감정을 분류합니다.
    - **Sentiment Analysis**: Uses a transformer-based model to classify the emotions of the text.
    - **키워드 추출 / Keyword Extraction**: KR-WordRank 알고리즘을 사용하여 텍스트에서 주요 키워드를 추출합니다.
    - **Keyword Extraction**: Uses the KR-WordRank algorithm to extract key keywords from the text.
  - **기술 / Technologies**: Python, BeautifulSoup, MongoDB, transformers, KR-WordRank

- **worker.js**
  - **기능**: Cloudflare Worker를 이용하여 HTTP 요청을 중계하는 Proxy 기능을 합니다. GET 요청은 차단하고, POST 요청만 처리합니다.
  - **Features**: Uses Cloudflare Worker to relay HTTP requests as a proxy. Blocks GET requests and only processes POST requests.
  - **기술 / Technologies**: JavaScript

### API Server
- **main.py**
  - **기능**: FastAPI를 사용하여 다양한 API 요청에 대해 응답하는 서버입니다. MongoDB에 연결하여 데이터를 처리합니다.
  - **Features**: A server that responds to various API requests using FastAPI. Connects to MongoDB to process data.
  - **API Endpoints**:
    - **Root (`/`)**: Returns a simple message indicating that the server is running.
    - **Top 5 News (`/news/{team_id}`)**: Returns the top 5 recent news articles for a specific team ID.
    - **Top 3 Positive News (`/news/positive/{team_id}`)**: Returns the top 3 positive news articles with sentiment scores above 0.6 for a specific team ID.
    - **Top 3 Negative News (`/news/negative/{team_id}`)**: Returns the top 3 negative news articles with sentiment scores below -0.6 for a specific team ID.
    - **SNS Data (`/sns/{team_id}`)**: Returns SNS data for a specific team ID.
  - **기술 / Technologies**: FastAPI, Python, MongoDB
