"""
키워드 분류기 테스트 스크립트

이 스크립트는 키워드 분류기를 실제 네이버 API를 사용하여 테스트합니다.
"""
import os
import sys
import json
import logging
from dotenv import load_dotenv
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# 테스트 함수
def test_keyword_classifier():
    """키워드 분류기 테스트"""
    from src.core.classifier.keyword_classifier import KeywordClassifier, KeywordType
    
    # 네이버 API 키 확인
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        logger.error("네이버 API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return
    
    # 키워드 분류기 초기화
    classifier = KeywordClassifier(
        client_id=client_id,
        client_secret=client_secret,
        save_results=True  # 검색 결과를 파일로 저장
    )
    
    # 테스트할 키워드 목록
    test_keywords = [
        "골밀도",           # 정보성 키워드 예상
        "아이폰 15",        # 상품성 키워드 예상
        "비타민D",          # 혼합 키워드 예상
        "삼성전자",         # 브랜드/회사명 예상
        "다이어트 방법"     # 정보성 키워드 예상
    ]
    
    # 결과 저장용 디렉토리 생성
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # 각 키워드에 대해 분류 수행
    results = []
    for keyword in test_keywords:
        logger.info(f"키워드 '{keyword}' 분류 시작")
        
        try:
            # 분류 수행
            result = classifier.classify(keyword)
            
            # 결과 출력
            print(f"\n===== 키워드 '{keyword}' 분석 결과 =====")
            print(f"유형: {result['type']}")
            print(f"신뢰도: {result['confidence']:.2f}")
            print(f"분석: {result['analysis']}")
            print(f"카테고리: {result['category']}")
            print(f"블로그 결과 수: {result['blog_count']}")
            print(f"쇼핑 결과 수: {result['shop_count']}")
            
            # 결과 저장
            results.append(result)
            
        except Exception as e:
            logger.error(f"키워드 '{keyword}' 분류 중 오류 발생: {str(e)}")
    
    # 전체 결과를 JSON 파일로 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = os.path.join(results_dir, f"classification_results_{timestamp}.json")
    
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"분류 결과가 {result_file}에 저장되었습니다.")

if __name__ == "__main__":
    print("=== 키워드 분류기 테스트 ===")
    test_keyword_classifier() 