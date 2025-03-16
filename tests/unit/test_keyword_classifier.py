"""
키워드 분류기 테스트

이 모듈은 KeywordClassifier 클래스의 기능을 테스트합니다.
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.classifier import KeywordClassifier, KeywordType
from src.core.classifier.keyword_classifier import KeywordClassifierConfig

class TestKeywordClassifier(unittest.TestCase):
    """KeywordClassifier 클래스에 대한 테스트"""
    
    def setUp(self):
        """테스트 환경을 설정합니다."""
        # 테스트용 환경 변수 설정
        os.environ["NAVER_CLIENT_ID"] = "test_client_id"
        os.environ["NAVER_CLIENT_SECRET"] = "test_client_secret"
        
        # 테스트용 분류기 설정
        config = KeywordClassifierConfig(
            llm_model="gpt-4o-mini",
            llm_temperature=0
        )
        self.classifier = KeywordClassifier(config=config)
    
    def test_init(self):
        """초기화 테스트"""
        self.assertIsNotNone(self.classifier)
        self.assertEqual(self.classifier.config.llm_model, "gpt-4o-mini")
        self.assertEqual(self.classifier.config.llm_temperature, 0)
    
    @patch("src.core.classifier.keyword_classifier.naver_search")
    def test_classify_keyword_information(self, mock_naver_search):
        """정보성 키워드 분류 테스트"""
        # 블로그 검색 결과 설정
        blog_res = {
            "items": [
                {
                    "title": "골밀도에 좋은 음식",
                    "description": "골밀도를 높이는 방법에 대한 글입니다."
                },
                {
                    "title": "골밀도 검사 방법",
                    "description": "골밀도 검사에 대한 설명입니다."
                }
            ]
        }
        
        # 쇼핑 검색 결과 설정 (비어있음)
        shop_res = {"items": []}
        
        # 네이버 검색 함수 모킹
        mock_naver_search.side_effect = lambda keyword, search_type: blog_res if search_type == "blog" else shop_res
        
        # 키워드 분류 실행
        result = self.classifier.classify_keyword("골밀도")
        
        # 검증
        self.assertEqual(result["type"], "information")
        self.assertGreater(result["confidence"], 0.5)
        self.assertIsNone(result["category"])
        self.assertEqual(len(result["titles"]), 2)
    
    @patch("src.core.classifier.keyword_classifier.naver_search")
    def test_classify_keyword_brand(self, mock_naver_search):
        """브랜드 키워드 분류 테스트"""
        # 블로그 검색 결과
        blog_res = {
            "items": [
                {
                    "title": "유팡 제품 사용기",
                    "description": "유팡 젖병소독기를 구매했습니다."
                }
            ]
        }
        
        # 쇼핑 검색 결과 (동일 브랜드)
        shop_res = {
            "items": [
                {"title": "유팡 젖병소독기", "brand": "유팡", "maker": "유팡코리아"},
                {"title": "유팡 젖병", "brand": "유팡", "maker": "유팡코리아"},
                {"title": "유팡 빨대컵", "brand": "유팡", "maker": "유팡코리아"},
                {"title": "유팡 이유식용기", "brand": "유팡", "maker": "유팡코리아"},
                {"title": "유팡 젖꼭지", "brand": "유팡", "maker": "유팡코리아"},
                {"title": "유팡 젖병세정제", "brand": "유팡", "maker": "유팡코리아"}
            ]
        }
        
        # 네이버 검색 함수 모킹
        mock_naver_search.side_effect = lambda keyword, search_type: blog_res if search_type == "blog" else shop_res
        
        # 키워드 분류 실행
        result = self.classifier.classify_keyword("유팡")
        
        # 검증
        self.assertEqual(result["type"], "brand")
        self.assertGreater(result["confidence"], 0.8)
        self.assertIsNone(result["category"])
    
    @patch("src.core.classifier.keyword_classifier.naver_search")
    @patch("src.core.classifier.keyword_classifier.KeywordClassifier.llm_classify_product_or_info")
    def test_classify_keyword_product(self, mock_llm_classify, mock_naver_search):
        """상품 키워드 분류 테스트"""
        # 블로그 검색 결과
        blog_res = {
            "items": [
                {
                    "title": "프리미엄견과류 추천",
                    "description": "맛있는 견과류 추천해드립니다."
                }
            ]
        }
        
        # 쇼핑 검색 결과 (다양한 브랜드)
        shop_res = {
            "items": [
                {"title": "A사 프리미엄견과류", "brand": "A사", "maker": "A식품", 
                 "category1": "식품", "category2": "간식", "category3": "견과류", "category4": ""},
                {"title": "B사 프리미엄견과류", "brand": "B사", "maker": "B식품",
                 "category1": "식품", "category2": "간식", "category3": "견과류", "category4": ""},
                {"title": "C사 프리미엄견과류", "brand": "C사", "maker": "C식품",
                 "category1": "식품", "category2": "간식", "category3": "견과류", "category4": ""},
                {"title": "D사 프리미엄견과류", "brand": "D사", "maker": "D식품",
                 "category1": "식품", "category2": "간식", "category3": "견과류", "category4": ""},
            ]
        }
        
        # 네이버 검색 함수 모킹
        mock_naver_search.side_effect = lambda keyword, search_type: blog_res if search_type == "blog" else shop_res
        
        # LLM 분류 함수 모킹
        mock_llm_classify.return_value = "상품"
        
        # 키워드 분류 실행
        result = self.classifier.classify_keyword("프리미엄견과류")
        
        # 검증
        self.assertEqual(result["type"], "product")
        self.assertGreater(result["confidence"], 0.5)
        self.assertIsNotNone(result["category"])
        self.assertEqual(result["category"][0], "식품")
        self.assertEqual(result["category"][2], "견과류")
    
    @patch("src.core.classifier.keyword_classifier.naver_search")
    def test_analyze_brand_consistency(self, mock_naver_search):
        """브랜드 일관성 분석 테스트"""
        # 일관성 있는 브랜드 데이터
        consistent_data = {
            "items": [
                {"title": "A 제품", "brand": "브랜드X", "maker": "제조사X"},
                {"title": "B 제품", "brand": "브랜드X", "maker": "제조사X"},
                {"title": "C 제품", "brand": "브랜드X", "maker": "제조사X"},
                {"title": "D 제품", "brand": "브랜드X", "maker": "제조사X"},
                {"title": "E 제품", "brand": "브랜드X", "maker": "제조사X"},
            ]
        }
        
        # 일관성 없는 브랜드 데이터
        inconsistent_data = {
            "items": [
                {"title": "A 제품", "brand": "브랜드A", "maker": "제조사A"},
                {"title": "B 제품", "brand": "브랜드B", "maker": "제조사B"},
                {"title": "C 제품", "brand": "브랜드C", "maker": "제조사C"},
                {"title": "D 제품", "brand": "브랜드D", "maker": "제조사D"},
                {"title": "E 제품", "brand": "브랜드E", "maker": "제조사E"},
            ]
        }
        
        # 일관성 있는 브랜드 분석
        result1 = self.classifier.analyze_brand_consistency(consistent_data)
        self.assertTrue(result1["is_consistent"])
        
        # 일관성 없는 브랜드 분석
        result2 = self.classifier.analyze_brand_consistency(inconsistent_data)
        self.assertFalse(result2["is_consistent"])
    
    def test_extract_high_frequency_categories(self):
        """고빈도 카테고리 추출 테스트"""
        # 테스트 데이터
        test_data = {
            "items": [
                {"category1": "식품", "category2": "간식", "category3": "견과류", "category4": ""},
                {"category1": "식품", "category2": "간식", "category3": "건조과일", "category4": ""},
                {"category1": "식품", "category2": "간식", "category3": "견과류", "category4": ""},
                {"category1": "식품", "category2": "건강식품", "category3": "영양제", "category4": ""},
                {"category1": "식품", "category2": "간식", "category3": "견과류", "category4": ""},
            ]
        }
        
        # 카테고리 추출
        result = self.classifier.extract_high_frequency_categories(test_data)
        
        # 검증
        self.assertEqual(result[0], "식품")  # category1 최빈값
        self.assertEqual(result[1], "간식")  # category2 최빈값
        self.assertEqual(result[2], "견과류")  # category3 최빈값
        
if __name__ == "__main__":
    unittest.main() 