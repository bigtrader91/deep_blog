# 키워드 분류기 모듈

이 모듈은 입력된 키워드를 다음 세 가지 카테고리로 분류합니다:

1. **브랜드 (Brand)**: 특정 브랜드나 회사 이름에 관련된 키워드
2. **상품 (Product)**: 구매 가능한 제품이나 서비스에 관련된 키워드
3. **정보성 (Information)**: 정보 제공이나 지식 공유 목적의 키워드

## 사용 방법

```python
from src.core.classifier import KeywordClassifier

# 기본 설정으로 분류기 생성
classifier = KeywordClassifier()

# 키워드 분류
result = classifier.classify_keyword("골밀도")
print(f"유형: {result['type']}")  # 'brand', 'product', 'information', 'unknown' 중 하나
print(f"신뢰도: {result['confidence']}")
print(f"분석: {result['analysis']}")
print(f"카테고리: {result['category']}")  # product 유형일 경우에만 값이 있음
```

## 동작 방식

분류 프로세스는 다음과 같은 단계로 진행됩니다:

1. **네이버 API 검색**: 주어진 키워드로 블로그와 쇼핑 검색을 수행합니다.
2. **브랜드 일관성 분석**: 쇼핑 검색 결과에서 브랜드/제조사 정보의 일관성을 분석합니다.
3. **LLM 기반 분류**: 브랜드가 아니라고 판단된 경우, LLM을 활용하여 상품인지 정보성인지 분류합니다.
4. **카테고리 추출**: 상품인 경우 네이버 쇼핑 결과에서 카테고리 정보를 추출합니다.

## 설정

분류기는 다음과 같은 설정을 지원합니다:

```python
from src.core.classifier import KeywordClassifier
from src.core.classifier.keyword_classifier import KeywordClassifierConfig

# 사용자 지정 설정으로 분류기 생성
config = KeywordClassifierConfig(
    llm_model="gpt-4o",  # LLM 모델 선택
    llm_temperature=0.3,  # 창의성 조절 (0: 결정적, 1: 창의적)
    min_brand_consistency=0.7,  # 브랜드 일관성 기준 (0~1)
    min_valid_items=3  # 브랜드 판단에 필요한 최소 아이템 수
)

classifier = KeywordClassifier(config=config)
```

## 환경 설정

네이버 API를 사용하기 위해 `.env` 파일에 다음 값을 설정해야 합니다:

```
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
``` 