# 네이버 검색 API 병렬 데이터 수집기

이 프로젝트는 네이버 검색 API를 사용하여 뉴스, 백과사전, 지식인에서 병렬로 데이터를 수집하고, 각 링크의 상세 내용까지 크롤링하는 도구입니다.

## 기능

- 네이버 뉴스, 백과사전, 지식인 API를 통한 검색 결과 수집
- 각 검색 결과 링크의 상세 내용 크롤링
- 비동기 처리를 통한 병렬 수집으로 성능 향상
- 크롤링봇 감지를 피하기 위한 기능 (랜덤 User-Agent, 랜덤 딜레이 등)
- 수집한 데이터를 JSON 형식으로 저장

## 사전 요구사항

- Python 3.9 이상
- 네이버 개발자 센터에서 발급받은 API 키
- 필요한 Python 패키지:
  - aiohttp
  - asyncio
  - beautifulsoup4
  - nest-asyncio
  - python-dotenv
  - requests

## 설치 방법

1. 이 레포지토리를 클론합니다.

```bash
git clone <repository-url>
```

2. 필요한 패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

3. 환경 변수 설정을 위한 `.env` 파일을 생성하고 네이버 API 키를 추가합니다.

```
NAVER_CLIENT_ID=네이버_애플리케이션_클라이언트_ID
NAVER_CLIENT_SECRET=네이버_애플리케이션_클라이언트_시크릿
```

## 사용 방법

### 명령줄에서 실행하기

```bash
# 기본 사용법
python src/data_crawler.py <검색어> [표시할 결과 수]

# 예시
python src/data_crawler.py "인공지능" 5
```

### 파이썬 코드에서 사용하기

```python
import asyncio
from src.data_crawler import NaverCrawler

async def example():
    # 크롤러 초기화
    crawler = NaverCrawler()
    
    # 검색어와 결과 수 설정
    query = "인공지능"
    display = 5
    
    # 병렬 크롤링 실행
    results = await crawler.crawl_all(query, display)
    
    # 결과 저장
    filename = crawler.save_results(results)
    print(f"결과가 {filename}에 저장되었습니다.")

# 비동기 함수 실행
asyncio.run(example())
```

### Jupyter Notebook에서 사용하기

제공된 `data_crawler_example.ipynb` 노트북을 참조하세요.

## 테스트

```bash
# 테스트 스크립트 실행
python src/test_data_crawler.py <검색어> [표시할 결과 수]

# 예시
python src/test_data_crawler.py "딥러닝" 3
```

## 주의사항

- 네이버 검색 API의 호출 한도가 있으므로 과도한 요청을 피해주세요.
- 웹사이트 크롤링 시 해당 사이트의 이용약관을 준수해야 합니다.
- 크롤링한 데이터를 상업적으로 이용할 경우 관련 법규와 라이선스를 확인해주세요.

## 코드 구조

- `src/data_crawler.py`: 메인 크롤러 클래스 및 기능 구현
- `src/test_data_crawler.py`: 크롤러 테스트 스크립트
- `data_crawler_example.ipynb`: Jupyter Notebook 예제

## 라이선스

MIT 라이선스 