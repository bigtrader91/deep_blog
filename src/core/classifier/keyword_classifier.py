"""
키워드 분류기 모듈

이 모듈은 검색 키워드를 분석하여 정보성 키워드인지 상품성 키워드인지 분류합니다.
"""
import os
import json
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

from src.core.search.utils import naver_search

# 로깅 설정
logger = logging.getLogger(__name__)

class KeywordType(str, Enum):
    """키워드 유형 열거형"""
    INFORMATION = "information"  # 정보성 키워드
    PRODUCT = "product"          # 상품성 키워드
    MIXED = "mixed"              # 혼합 키워드
    UNKNOWN = "unknown"          # 알 수 없음

@dataclass
class KeywordClassifierConfig:
    """키워드 분류기 설정"""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0
    min_brand_consistency: float = 0.7
    min_valid_items: int = 5

class KeywordClassifier:
    """
    키워드 분류기 클래스
    
    검색 키워드를 분석하여 정보성 키워드인지 상품성 키워드인지 분류합니다.
    """
    
    def __init__(self, 
                 client_id: Optional[str] = None, 
                 client_secret: Optional[str] = None,
                 save_results: bool = False,
                 config: Optional[KeywordClassifierConfig] = None):
        """
        키워드 분류기 초기화
        
        Args:
            client_id: 네이버 API 클라이언트 ID
            client_secret: 네이버 API 클라이언트 시크릿
            save_results: 검색 결과 저장 여부
            config: 분류기 설정
        """
        self.client_id = client_id or os.environ.get("NAVER_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("NAVER_CLIENT_SECRET")
        self.save_results = save_results
        self.config = config or KeywordClassifierConfig()
        
        if not self.client_id or not self.client_secret:
            logger.warning("네이버 API 인증 정보가 설정되지 않았습니다.")
        
        # 환경 변수에 API 키 설정
        if self.client_id:
            os.environ["NAVER_CLIENT_ID"] = self.client_id
        if self.client_secret:
            os.environ["NAVER_CLIENT_SECRET"] = self.client_secret
    
    def classify(self, keyword: str) -> Dict[str, Any]:
        """
        키워드 분류 수행
        
        Args:
            keyword: 분류할 키워드
            
        Returns:
            분류 결과 딕셔너리
        """
        logger.info(f"키워드 '{keyword}' 분류 시작")
        
        # 블로그 검색 결과 가져오기
        blog_results = self._search_blog(keyword)
        
        # 쇼핑 검색 결과 가져오기
        shop_results = self._search_shop(keyword)
        
        # 결과 분석
        result = self._analyze_results(keyword, blog_results, shop_results)
        
        logger.info(f"키워드 '{keyword}' 분류 완료: {result['type']}")
        return result
    
    # 기존 코드와의 호환성을 위한 alias
    classify_keyword = classify
    
    def _search_blog(self, keyword: str) -> Dict[str, Any]:
        """
        블로그 검색 수행
        
        Args:
            keyword: 검색할 키워드
            
        Returns:
            블로그 검색 결과
        """
        try:
            return naver_search(
                keyword=keyword,
                search_type="blog",
                save_results=self.save_results
            )
        except Exception as e:
            logger.error(f"블로그 검색 중 오류 발생: {str(e)}")
            return {"items": []}
    
    def _search_shop(self, keyword: str) -> Dict[str, Any]:
        """
        쇼핑 검색 수행
        
        Args:
            keyword: 검색할 키워드
            
        Returns:
            쇼핑 검색 결과
        """
        try:
            return naver_search(
                keyword=keyword,
                search_type="shop",
                save_results=self.save_results
            )
        except Exception as e:
            logger.error(f"쇼핑 검색 중 오류 발생: {str(e)}")
            return {"items": []}
    
    def _analyze_results(self, 
                         keyword: str, 
                         blog_results: Dict[str, Any], 
                         shop_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        검색 결과 분석
        
        Args:
            keyword: 검색 키워드
            blog_results: 블로그 검색 결과
            shop_results: 쇼핑 검색 결과
            
        Returns:
            분석 결과 딕셔너리
        """
        blog_count = len(blog_results.get("items", []))
        shop_count = len(shop_results.get("items", []))
        
        # 카테고리 정보 추출
        categories = self._extract_categories(shop_results)
        
        # 브랜드/제조사 일관성 분석
        brand_analysis = self._analyze_brand_consistency(shop_results)
        
        # 신뢰도 및 유형 결정
        if brand_analysis["is_consistent"]:
            # 브랜드 일관성이 높으면 브랜드로 분류
            keyword_type = KeywordType.PRODUCT
            confidence = 0.9
            analysis = f"브랜드/회사명으로 분석됨 (브랜드 일관성: {brand_analysis['consistency_ratio']:.2f})"
        elif blog_count > 0 and shop_count == 0:
            keyword_type = KeywordType.INFORMATION
            confidence = 0.9
            analysis = "정보성 키워드로 분석됨 (쇼핑 결과 없음)"
        elif shop_count > 0 and blog_count == 0:
            keyword_type = KeywordType.PRODUCT
            confidence = 0.9
            analysis = "상품성 키워드로 분석됨 (블로그 결과 없음)"
        elif shop_count > blog_count * 2:
            keyword_type = KeywordType.PRODUCT
            confidence = 0.7
            analysis = "상품성 키워드로 분석됨 (쇼핑 결과가 블로그 결과보다 많음)"
        elif blog_count > shop_count * 2:
            keyword_type = KeywordType.INFORMATION
            confidence = 0.7
            analysis = "정보성 키워드로 분석됨 (블로그 결과가 쇼핑 결과보다 많음)"
        elif blog_count > 0 and shop_count > 0:
            # 블로그 제목 분석으로 정보성 키워드 여부 판단
            if self._is_informational_content(blog_results):
                keyword_type = KeywordType.INFORMATION
                confidence = 0.65
                analysis = "정보성 키워드로 분석됨 (블로그 내용 분석 기반)"
            else:
                keyword_type = KeywordType.MIXED
                confidence = 0.6
                analysis = "혼합 키워드로 분석됨 (블로그 및 쇼핑 결과 모두 존재)"
        else:
            keyword_type = KeywordType.UNKNOWN
            confidence = 0.5
            analysis = "분류 불가 (충분한 검색 결과 없음)"
        
        # 결과 구성
        result = {
            "keyword": keyword,
            "type": keyword_type,
            "confidence": confidence,
            "analysis": analysis,
            "category": categories[0] if categories else None,
            "categories": categories,
            "blog_count": blog_count,
            "shop_count": shop_count,
            "brand_analysis": brand_analysis,
            "titles": [item.get("title", "") for item in blog_results.get("items", [])],
            "description": [item.get("description", "") for item in blog_results.get("items", [])],
            "timestamp": datetime.now().isoformat()
        }
        
        return result
    
    def _extract_categories(self, shop_results: Dict[str, Any]) -> List[str]:
        """
        쇼핑 검색 결과에서 카테고리 정보 추출
        
        Args:
            shop_results: 쇼핑 검색 결과
            
        Returns:
            카테고리 목록
        """
        categories = []
        for item in shop_results.get("items", []):
            for i in range(1, 5):
                category = item.get(f"category{i}")
                if category and category not in categories:
                    categories.append(category)
        
        return categories
    
    def _analyze_brand_consistency(self, shop_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        쇼핑 검색 결과에서 브랜드/제조사의 일관성을 분석
        
        Args:
            shop_results: 쇼핑 검색 결과
            
        Returns:
            브랜드 일관성 분석 결과
        """
        items = shop_results.get("items", [])
        if not items:
            return {
                "is_consistent": False,
                "consistency_ratio": 0.0,
                "most_common_brand": None,
                "most_common_maker": None
            }
        
        # 브랜드/제조사 정보 추출
        brands = {}
        makers = {}
        
        for item in items:
            brand = item.get("brand", "").strip()
            maker = item.get("maker", "").strip()
            
            if brand:
                brands[brand] = brands.get(brand, 0) + 1
            if maker:
                makers[maker] = makers.get(maker, 0) + 1
        
        # 가장 많이 등장한 브랜드/제조사 찾기
        most_common_brand = max(brands.items(), key=lambda x: x[1])[0] if brands else None
        most_common_maker = max(makers.items(), key=lambda x: x[1])[0] if makers else None
        
        # 일관성 비율 계산
        brand_consistency = brands.get(most_common_brand, 0) / len(items) if most_common_brand else 0
        maker_consistency = makers.get(most_common_maker, 0) / len(items) if most_common_maker else 0
        
        # 브랜드 또는 제조사 일관성 중 더 높은 값 사용
        consistency_ratio = max(brand_consistency, maker_consistency)
        
        # 일관성이 설정값 이상이면 일관성 있음으로 판단
        is_consistent = consistency_ratio >= self.config.min_brand_consistency
        
        return {
            "is_consistent": is_consistent,
            "consistency_ratio": consistency_ratio,
            "most_common_brand": most_common_brand,
            "most_common_maker": most_common_maker
        }
    
    def _is_informational_content(self, blog_results: Dict[str, Any]) -> bool:
        """
        블로그 검색 결과가 정보성 콘텐츠인지 분석
        
        Args:
            blog_results: 블로그 검색 결과
            
        Returns:
            정보성 콘텐츠 여부
        """
        # 정보성 콘텐츠를 나타내는 키워드
        info_keywords = [
            "방법", "효과", "증상", "원인", "차이", "종류", 
            "특징", "장점", "단점", "비교", "추천", "리뷰",
            "사용법", "활용", "예방", "관리", "치료", "개선",
            "해결", "대처", "팁", "노하우", "가이드", "설명"
        ]
        
        # 블로그 제목과 설명에서 정보성 키워드 찾기
        info_keyword_count = 0
        total_items = len(blog_results.get("items", []))
        
        if total_items == 0:
            return False
        
        for item in blog_results.get("items", []):
            title = item.get("title", "")
            description = item.get("description", "")
            
            # HTML 태그 제거
            title = title.replace("<b>", "").replace("</b>", "")
            description = description.replace("<b>", "").replace("</b>", "")
            
            # 정보성 키워드 확인
            for keyword in info_keywords:
                if keyword in title or keyword in description:
                    info_keyword_count += 1
                    break
        
        # 50% 이상의 결과가 정보성 키워드를 포함하면 정보성 콘텐츠로 판단
        return info_keyword_count / total_items >= 0.5
    
    def llm_classify_product_or_info(self, keyword: str) -> str:
        """
        LLM을 사용하지 않고 간단한 규칙 기반으로 상품/정보성 구분
        
        Args:
            keyword: 분류할 키워드
            
        Returns:
            '상품' 또는 '정보성'
        """
        # 상품성 키워드로 판단할 단어들
        product_keywords = ['구매', '할인', '세일', '쇼핑', '제품', '상품', '가격', 
                           '구입', '주문', '도서', '의류', '가구', '책상', '의자']
        
        # 정보성 키워드로 판단할 단어들
        info_keywords = ['방법', '정보', '리뷰', '후기', '평가', '비교', '분석', '증상', 
                        '치료', '질환', '효능', '효과', '예방', '건강', '운동', '다이어트']
        
        # 키워드 내에 상품성/정보성 관련 단어가 있는지 확인
        for word in product_keywords:
            if word in keyword:
                return "상품"
        
        for word in info_keywords:
            if word in keyword:
                return "정보성"
        
        # 기본값은 정보성
        return "정보성"

# 테스트 코드
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 키워드 분류기 생성
    classifier = KeywordClassifier()
    
    # 테스트 키워드
    test_keywords = ["골밀도", "프리미엄견과류", "어린이날여행", "유팡", "MIMAXARI"]
    
    for kw in test_keywords:
        print(f"\n===== 키워드 '{kw}' 분석 =====")
        result = classifier.classify(kw)
        print(f"유형: {result['type']}")
        print(f"신뢰도: {result['confidence']:.2f}")
        print(f"분석: {result['analysis']}")
        print(f"카테고리: {result['category']}")
        if result['titles']:
            print(f"제목 샘플: {result['titles'][:2]}")
        if result['description']:
            print(f"설명 샘플: {result['description'][:2]}") 