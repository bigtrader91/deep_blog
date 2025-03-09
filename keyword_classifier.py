import os
import urllib.request
import urllib.parse
import json
from typing import Dict, List, TypedDict, Any, Optional
from dotenv import load_dotenv

# ----- langchain + openai_functions 관련 임포트
from langchain.chains.openai_functions import create_structured_output_runnable
# (환경에 맞게 langchain 관련 패키지를 교체하세요)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

load_dotenv()  # .env에서 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 로드

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# --------------------
# 1) TypedDict 정의
# --------------------
class KeywordType(TypedDict):
    """키워드 분류 결과 타입"""
    keyword: str
    type: str           # 'brand', 'information', 'product'
    confidence: float
    analysis: str
    category: Optional[List[str]]  # 상품 키워드인 경우, [고빈도 category1, category2, category3, category4]

# --------------------
# 2) 네이버 쇼핑 검색 함수
# --------------------
def naver_search(query: str, search_type: str = "shop") -> Dict[str, Any]:
    """
    네이버 API를 사용하여 검색 결과를 가져옵니다.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 환경 변수에 설정해야 합니다.")
    
    enc_text = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/{search_type}.json?query={enc_text}"
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
    
    try:
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        if rescode == 200:
            return json.loads(response.read().decode('utf-8'))
        else:
            print("Error Code:", rescode)
            return {}
    except Exception as e:
        print("검색 중 예외 발생:", e)
        return {}

# --------------------
# 3) 브랜드 일관성 분석
# --------------------
def analyze_brand_consistency(search_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    검색 결과에서 브랜드/제조사의 일관성을 분석합니다.
    """
    if not search_results or "items" not in search_results:
        return {"is_consistent": False, "analysis": "검색 결과가 없습니다.", "analysis_detail": {}}
    
    items = search_results.get("items", [])
    if not items:
        return {"is_consistent": False, "analysis": "검색 결과 아이템이 없습니다.", "analysis_detail": {}}
    
    # 브랜드/제조사 정보 추출
    brands = [item.get("brand", "").strip() for item in items if "brand" in item]
    makers = [item.get("maker", "").strip() for item in items if "maker" in item]
    
    valid_brands = [b for b in brands if b]
    valid_makers = [m for m in makers if m]
    
    unique_brands = set(valid_brands)
    unique_makers = set(valid_makers)
    
    brand_counts = {brand: valid_brands.count(brand) for brand in unique_brands}
    maker_counts = {maker: valid_makers.count(maker) for maker in unique_makers}
    
    # 브랜드/메이커 중 가장 많이 등장한 횟수 계산
    brand_consistency_ratio = 0.0
    if valid_brands:
        most_freq_brand_count = max(brand_counts.values())
        brand_consistency_ratio = most_freq_brand_count / len(valid_brands)
    
    maker_consistency_ratio = 0.0
    if valid_makers:
        most_freq_maker_count = max(maker_counts.values())
        maker_consistency_ratio = most_freq_maker_count / len(valid_makers)
    
    # 80% 이상의 상품이 동일 브랜드 또는 maker + 충분한 아이템 수가 있어야 브랜드 일관성 있음으로 판단
    is_consistent = False
    if (brand_consistency_ratio >= 0.8 and len(valid_brands) >= 5) or \
       (maker_consistency_ratio >= 0.8 and len(valid_makers) >= 5):
        is_consistent = True
    
    analysis_detail = {
        "total_items": len(items),
        "valid_brand_count": len(valid_brands),
        "valid_maker_count": len(valid_makers),
        "brand_counts": brand_counts,
        "maker_counts": maker_counts,
        "brand_consistency_ratio": brand_consistency_ratio,
        "maker_consistency_ratio": maker_consistency_ratio,
    }
    return {
        "is_consistent": is_consistent,
        "analysis": f"브랜드 일관성 {is_consistent}",
        "analysis_detail": analysis_detail
    }

# --------------------
# 4) 각 category 필드별 고빈도 카테고리 추출 함수
# --------------------
def extract_high_frequency_categories(search_results: Dict[str, Any]) -> List[str]:
    """
    네이버 쇼핑 검색 결과에서 각 category1 ~ category4 필드의 고빈도(최다 등장) 값을 추출합니다.
    결과는 [고빈도 category1, 고빈도 category2, 고빈도 category3, 고빈도 category4] 형식의 리스트로 반환됩니다.
    """
    high_freq_categories = []
    for key in ['category1', 'category2', 'category3', 'category4']:
        freq = {}
        for item in search_results.get("items", []):
            value = item.get(key, "").strip()
            if value:
                freq[value] = freq.get(value, 0) + 1
        if freq:
            most_freq = max(freq, key=freq.get)
            high_freq_categories.append(most_freq)
        else:
            high_freq_categories.append("")
    return high_freq_categories

# --------------------
# 5) LLM으로 '상품 vs 정보성' 분류하기
#    - 브랜드가 아닌 경우에만 활용
# --------------------
class LLMClassificationResult(BaseModel):
    """LLM이 최종 분류를 반환"""
    classification: str = Field(..., description="분류 결과. '상품' 또는 '정보성' 중 하나를 예상")

class LLMGenerateTitle(BaseModel):
    """LLM이 제목 생성"""
    title: str = Field(..., description="제목 생성")

classification_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
title_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

classification_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "당신은 네이버 쇼핑검색 결과에 대한 전문 분석가입니다. "
        "입력으로 {keyword}가 주어집니다. "
        "단, 이미 '브랜드'가 아님은 확정된 상태이므로, "
        "'상품' 혹은 '정보성' 중 하나를 한국어로 결정해 주세요."
    ),
    (
        "human",
        "검색결과를 분석하여 '{keyword}'가 '상품'인지 '정보성'인지 판단해 주세요. "
        "단, 브랜드는 이미 제외된 상태입니다."
    ),
])

title_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "당신은 블로그 제목을 생성하는 전문가입니다. "
        "입력으로 키워드, 타이틀, 설명들이 주어집니다. "
        "키워드와 타이틀, 설명들을 참고하여 적절한 제목을 생성해 주세요. "
        "리뷰와 관련된 제목은 배제하여주세요 "
    ),
    (
        "human",
        "아래 데이터를 참고하여 적절한 제목을 생성해 주세요. "
        "{data}"
    ),
])
classification_llm_chain = classification_prompt | classification_llm.with_structured_output(LLMClassificationResult)
title_llm_chain = title_prompt | title_llm.with_structured_output(LLMGenerateTitle)


def llm_classify_product_or_info(keyword: str) -> str:
    """
    LLM을 이용해 '상품' vs '정보성' 분류
    """
    try:
        result = classification_llm_chain.invoke({"keyword": keyword})
        return result.classification
    except Exception as e:
        print("LLM 분류 에러:", e)
        return "정보성"

def llm_generate_title(data: str) -> str:
    """
    LLM을 이용해 제목 생성
    """
    try:
        result = title_llm_chain.invoke({"data": data})
        return result.title
    except Exception as e:
        print("LLM 제목 생성 에러:", e)
        return "제목 생성 불가"

# --------------------
# 6) 최종 분류 함수
#    - (1) 브랜드 분석 -> 일관성 있으면 'brand'
#    - (2) 브랜드가 아니면 LLM으로 '상품' vs '정보성' 판별
#    - 상품성 키워드인 경우, 고빈도 category 리스트 추가 (정보성은 비워둠)
# --------------------
def classify_keyword(keyword: str) -> KeywordType:
    """
    주어진 키워드가 'brand', 'information', 'product' 중 어느 유형인지 최종 분류합니다.
    상품성 키워드인 경우에는 네이버 쇼핑 검색 결과에서 각 category 필드별 고빈도 값을 추출하여 리스트로 추가합니다.
    만약 type이 information이면 category 필드는 비워둡니다.
    """
    try:
        # 1) 네이버 쇼핑 검색
        shop_res = naver_search(keyword, "shop")
        if not shop_res or "items" not in shop_res or not shop_res["items"]:
            # 검색 결과 없으면 blog 검색 진행
            blog_res = naver_search(keyword, "blog")
            blog_cnt = len(blog_res["items"]) if blog_res and "items" in blog_res else 0
            
            if blog_cnt > 0:
                return {
                    "keyword": keyword,
                    "type": "information",
                    "confidence": 0.7,
                    "analysis": f"쇼핑 검색 결과가 없고, 블로그 결과 {blog_cnt}개 => 정보성 키워드로 추정",
                    "category": None
                }
            else:
                return {
                    "keyword": keyword,
                    "type": "unknown",
                    "confidence": 0.0,
                    "analysis": "검색 결과가 전혀 없습니다.",
                    "category": None
                }
        
        # 2) 브랜드 일관성 분석
        brand_analysis = analyze_brand_consistency(shop_res)
        if brand_analysis["is_consistent"]:
            detail = brand_analysis["analysis_detail"]
            confidence = max(detail["brand_consistency_ratio"], detail["maker_consistency_ratio"])
            confidence = min(confidence + 0.1, 1.0)  # 약간 상승 조정
            
            # 브랜드로 분류하는 경우는 상품 카테고리 리스트를 추가하지 않음 (혹은 별도 처리 가능)
            return {
                "keyword": keyword,
                "type": "brand",
                "confidence": confidence,
                "analysis": f"브랜드 일관성 {confidence*100:.1f}%. 계량적으로 브랜드로 판단",
                "category": None
            }
        else:
            # 브랜드가 아니라면 LLM으로 '상품' vs '정보성' 판별
            classification = llm_classify_product_or_info(keyword)
            
            if classification == "상품":
                # 상품성 키워드: 네이버 쇼핑 결과에서 각 category 필드별 고빈도 값 추출
                high_freq_categories = extract_high_frequency_categories(shop_res)
                return {
                    "keyword": keyword,
                    "type": "product",
                    "confidence": 0.8,  # 임의로 0.8 부여
                    "analysis": "LLM 분류 결과: 상품",
                    "category": high_freq_categories
                }
            else:
                return {
                    "keyword": keyword,
                    "type": "information",
                    "confidence": 0.8,
                    "analysis": "LLM 분류 결과: 정보성",
                    "category": None
                }
    except Exception as e:
        import traceback
        return {
            "keyword": keyword,
            "type": "unknown",
            "confidence": 0.0,
            "analysis": f"분류 중 예외 발생: {str(e)}\n{traceback.format_exc()}",
            "category": None
        }

# --------------------
# 7) 테스트
# --------------------
if __name__ == "__main__":
    test_keywords = ["골밀도", "프리미엄견과류", "어린이날여행", "유팡", "MIMAXARI"]  
    for kw in test_keywords:
        print(f"\n===== 키워드 '{kw}' 분석 =====")
        result = classify_keyword(kw)
        print(f"유형: {result['type']}")
        print(f"신뢰도: {result['confidence']:.2f}")
        print(f"분석: {result['analysis']}")
        print(f"카테고리: {result['category']}")
