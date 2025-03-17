# Deep Blog Generator

LLM과 웹 검색을 활용한 고품질 블로그 포스트 자동 생성 시스템

## 개요

Deep Blog Generator는 인공지능을 활용하여 다양한 주제에 대한 고품질 블로그 포스트를 자동으로 생성하는 시스템입니다. 이 시스템은 다음과 같은 특징을 가지고 있습니다:

1. **지능형 섹션 계획**: 주제를 분석하여 논리적인 블로그 섹션 구조를 계획합니다.
2. **다중 검색 엔진 통합**: Tavily, Perplexity, Exa 등 다양한 검색 엔진을 활용하여 정확한 정보를 수집합니다.
3. **학술 정보 검색**: arXiv, PubMed 검색을 통해 학술적 정보를 수집합니다.
4. **반복적 연구 프로세스**: 섹션 품질을 평가하고 필요한 경우 추가 연구를 수행합니다.
5. **자연스러운 통합**: 개별 섹션을 하나의 일관된 블로그 포스트로 결합합니다.

## 시스템 아키텍처

시스템은 다음과 같은 주요 구성 요소로 이루어져 있습니다:

- **API 서버**: FastAPI 기반 웹 서버로 외부 애플리케이션과의 인터페이스를 제공합니다.
- **워크플로우 엔진**: LangGraph를 활용한 워크플로우 시스템으로 블로그 생성 과정을 조율합니다.
- **검색 모듈**: 다양한 검색 엔진을 통해 주제 관련 정보를 수집합니다.
- **LLM 통합**: 언어 모델을 활용하여 계획 수립, 콘텐츠 작성, 품질 평가를 수행합니다.

## 설치 방법

### 요구 사항

- Python 3.9+
- 가상 환경 (선택사항이지만 권장)

### 설치 단계

1. 저장소 복제:
```
git clone https://github.com/your-username/deep_blog.git
cd deep_blog
```

2. 가상 환경 생성 및 활성화:
```
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 의존성 설치:
```
pip install -r requirements.txt
```

4. 환경 변수 설정:
`.env` 파일을 생성하고 필요한 API 키를 추가합니다:
```
ANTHROPIC_API_KEY=your_anthropic_api_key
TAVILY_API_KEY=your_tavily_api_key
# 추가 API 키
```

## 사용 방법

### API 서버 실행

```
python -m src.app
```

서버는 기본적으로 http://localhost:8000 에서 실행됩니다.

### API 엔드포인트

1. **블로그 생성 요청**:
```
POST /blog
```
예시 요청:
```json
{
  "topic": "인공지능의 윤리적 고려사항",
  "config": {
    "number_of_blog_sections": 5,
    "number_of_queries": 3,
    "max_search_depth": 2
  }
}
```

2. **생성 상태 확인**:
```
GET /blog/{job_id}
```

3. **서버 상태 확인**:
```
GET /health
```

## 주요 기능 설명

### 1. 섹션 계획 수립

주제를 분석하여 블로그 포스트의 구조를 계획합니다. 각 섹션은 주제의 다른 측면을 다루며, 서론과 결론을 포함합니다.

### 2. 정보 검색

계획된 각 섹션에 대해:
- 검색 쿼리를 생성합니다.
- 여러 검색 엔진을 통해 관련 정보를 수집합니다.
- 수집된 정보를 작성 프로세스에 사용할 수 있도록 처리합니다.

### 3. 콘텐츠 작성

수집된 정보를 기반으로 각 섹션의 내용을 작성합니다. 작성된 내용은 다음 기준으로 평가됩니다:
- 정확성: 내용의 사실 여부
- 관련성: 주제와의 연관성
- 완전성: 주제 커버리지
- 구성: 논리적 흐름
- 가독성: 이해 용이성

### 4. 품질 평가 및 추가 연구

각 섹션의 품질을 평가하고, 필요한 경우 추가 쿼리를 생성하여 더 많은 정보를 수집합니다.

### 5. 최종 통합

모든 섹션을 하나의 일관된 블로그 포스트로 통합합니다.

## 구성 옵션

블로그 생성 요청 시 다음과 같은 구성 옵션을 제공할 수 있습니다:

- `planner_provider`: 계획 모델 제공자 (기본값: "anthropic")
- `planner_model`: 계획에 사용할 모델 (기본값: "claude-3-7-sonnet-latest")
- `writer_provider`: 작성 모델 제공자 (기본값: "anthropic")
- `writer_model`: 작성에 사용할 모델 (기본값: "claude-3-7-sonnet-latest")
- `searcher_provider`: 검색 엔진 제공자 (기본값: "tavily")
- `number_of_blog_sections`: 블로그 섹션 수 (기본값: 5)
- `number_of_queries`: 섹션당 검색 쿼리 수 (기본값: 3)
- `max_search_depth`: 섹션당 최대 검색 반복 횟수 (기본값: 2)

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 새로운 기능: 마크다운 변환기

Deep Blog 프로젝트에 마크다운을 HTML로 변환하는 기능이 추가되었습니다. 이 기능은 다음과 같은 특징을 가지고 있습니다:

- LangChain과 LangGraph를 활용한 워크플로우 기반 변환
- 문서 내용에 기반한 자동 테마 추천
- 목차(TOC) 자동 생성
- 깔끔하고 스타일이 적용된 HTML 출력

### 사용 방법

```python
from src.app import markdown_to_html

# 기본 사용법
html_result = markdown_to_html("# 제목\n\n내용...")

# 테마 지정
html_result = markdown_to_html("# 제목\n\n내용...", theme_name="purple")

# 파일로 저장
html_result = markdown_to_html("# 제목\n\n내용...", 
                               theme_name="green", 
                               output_path="output.html")
```

### 예제 실행

```bash
# 예제 스크립트 실행
python examples/markdown_converter_example.py
```

### 설치 및 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
# .env 파일에 OPENAI_API_KEY=your_api_key 추가
```