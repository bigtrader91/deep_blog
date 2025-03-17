"""
네이버 API 사용 예제

이 스크립트는 네이버 검색 API와 네이버 검색광고 API 사용법을 보여줍니다.
"""
import json
import os
from pprint import pprint
import dotenv

# 환경 변수 로드
dotenv.load_dotenv()

# 네이버 API 유틸리티 임포트
from src.core.search.utils import (
    naver_search, 
    get_relkeyword, 
    get_keyword_trend,
    collect_related_keywords
)

def main():
    """예제 실행 메인 함수"""
    # API 키 설정 확인
    if not (os.getenv("NAVER_CLIENT_ID") and os.getenv("NAVER_CLIENT_SECRET")):
        print("환경 변수에 네이버 검색 API 키가 설정되어 있지 않습니다.")
        print("다음 환경 변수를 설정해주세요:")
        print("- NAVER_CLIENT_ID: 네이버 API 클라이언트 ID")
        print("- NAVER_CLIENT_SECRET: 네이버 API 클라이언트 시크릿")
    
    if not (os.getenv("NAVER_API_KEY") and os.getenv("NAVER_SECRET_KEY") and os.getenv("NAVER_CUSTOMER_ID")):
        print("환경 변수에 네이버 검색광고 API 키가 설정되어 있지 않습니다.")
        print("다음 환경 변수를 설정해주세요:")
        print("- NAVER_API_KEY: 네이버 검색광고 API 키")
        print("- NAVER_SECRET_KEY: 네이버 검색광고 시크릿 키")
        print("- NAVER_CUSTOMER_ID: 네이버 검색광고 고객 ID")
        return
    
    # 예제 1: 네이버 블로그 검색
    print("\n[예제 1] 네이버 블로그 검색")
    keyword = "건강 식품"
    print(f"키워드 '{keyword}'로 블로그 검색:")
    
    result = naver_search(
        keyword=keyword,
        search_type="blog",
        display=5,
        sort="sim",
        save_results=True
    )
    
    if "error" not in result:
        print(f"총 {result.get('total', 0)}개의 결과 중 상위 {len(result.get('items', []))}개:")
        for idx, item in enumerate(result.get("items", []), 1):
            print(f"{idx}. {item.get('title', '')}")
            print(f"   - 블로그명: {item.get('bloggername', '')}")
            print(f"   - 링크: {item.get('link', '')}")
            print(f"   - 작성일: {item.get('postdate', '')}")
            print()
    else:
        print(f"검색 실패: {result.get('error')}")
    
    # 예제 2: 연관 키워드 조회
    print("\n[예제 2] 연관 키워드 조회")
    keyword = "비타민"
    print(f"키워드 '{keyword}'의 연관 키워드:")
    
    result = get_relkeyword(keyword)
    
    if "error" not in result and "keywordList" in result:
        keywords = result["keywordList"]
        print(f"총 {len(keywords)}개의 연관 키워드 중 상위 5개:")
        for idx, item in enumerate(keywords[:5], 1):
            rel_keyword = item.get("relKeyword", "")
            pc_count = item.get("monthlyPcQcCnt", "0")
            mobile_count = item.get("monthlyMobileQcCnt", "0")
            competition = item.get("compIdx", 0)
            
            print(f"{idx}. {rel_keyword}")
            print(f"   - PC 검색수: {pc_count}")
            print(f"   - 모바일 검색수: {mobile_count}")
            print(f"   - 경쟁 정도: {competition}")
            print()
    else:
        print(f"연관 키워드 조회 실패: {result.get('error', '알 수 없는 오류')}")
    
    # 예제 3: 포맷팅된 연관 키워드 수집
    print("\n[예제 3] 포맷팅된 연관 키워드 수집")
    keyword = "프로바이오틱스"
    print(f"키워드 '{keyword}'의 연관 키워드 포맷팅:")
    
    result = collect_related_keywords(keyword, save_results=True)
    
    if "error" not in result and "relKeywords" in result:
        keywords = result["relKeywords"]
        print(f"총 {len(keywords)}개의 연관 키워드 중 상위 5개:")
        for idx, item in enumerate(keywords[:5], 1):
            rel_keyword = item.get("relKeyword", "")
            total_count = item.get("totalSearchCount", 0)
            competition = item.get("competition", "")
            
            print(f"{idx}. {rel_keyword}")
            print(f"   - 총 검색수: {total_count}")
            print(f"   - 경쟁 정도: {competition}")
            print()
    else:
        print(f"연관 키워드 수집 실패: {result.get('error', '알 수 없는 오류')}")
    
    # 예제 4: 트렌드 키워드 조회
    print("\n[예제 4] 트렌드 키워드 조회")
    keyword = "건강식품"
    print(f"키워드 '{keyword}'의 트렌드 조회:")
    
    result = get_keyword_trend(
        keyword=keyword,
        time_unit="month",
        device="all",
        ages=["3", "4", "5"]  # 20-34세
    )
    
    if "error" not in result:
        print("트렌드 조회 성공!")
        # 전체 JSON을 출력하는 대신 일부만 출력
        print("트렌드 데이터 샘플:")
        trend_sample = {k: v for k, v in result.items() if k != "keywordList"}
        pprint(trend_sample)
    else:
        print(f"트렌드 조회 실패: {result.get('error', '알 수 없는 오류')}")

if __name__ == "__main__":
    main() 