"""
네이버 키워드 수집기 예제

이 스크립트는 네이버 키워드 수집기 사용법을 보여줍니다.
"""
import asyncio
import pandas as pd
from datetime import datetime
import os
import dotenv

# 환경 변수 로드
dotenv.load_dotenv()

# 네이버 키워드 수집기 임포트
from src.core.search.engines import NaverKeywordCollector

async def main():
    """예제 실행 메인 함수"""
    # API 키 설정 확인
    api_key = os.getenv("NAVER_API_KEY")
    secret_key = os.getenv("NAVER_SECRET_KEY")
    customer_id = os.getenv("NAVER_CUSTOMER_ID")
    
    if not (api_key and secret_key and customer_id):
        print("환경 변수에 네이버 API 키가 설정되어 있지 않습니다.")
        print("다음 환경 변수를 설정해주세요:")
        print("- NAVER_API_KEY: 네이버 검색광고 API 키")
        print("- NAVER_SECRET_KEY: 네이버 검색광고 시크릿 키")
        print("- NAVER_CUSTOMER_ID: 네이버 검색광고 고객 ID")
        return
    
    # 키워드 수집기 초기화
    collector = NaverKeywordCollector(headless=True)
    print("네이버 키워드 수집기 초기화 완료")
    
    try:
        # 예제 1: 정보성 키워드 수집
        print("\n[예제 1] 건강 카테고리 정보성 키워드 수집")
        info_url = "https://kin.naver.com/qna/list.naver?dirId=7"
        
        print(f"URL에서 정보성 키워드 수집 시작: {info_url}")
        df_info = collector.collect_info_keywords_from_category(info_url, pages=2)
        
        if not df_info.empty:
            print(f"수집된 정보성 키워드: {len(df_info)}개")
            print("상위 5개 키워드:")
            print(df_info.head(5))
            
            # 엑셀로 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"info_keywords_{timestamp}.xlsx"
            df_info.to_excel(filename)
            print(f"정보성 키워드 저장 완료: {filename}")
        else:
            print("정보성 키워드를 찾지 못했습니다.")
        
        # 예제 2: 상품 키워드 수집 (비동기)
        print("\n[예제 2] 상품 키워드 비동기 수집")
        df_product, filename = await collector.collect_keywords_async(keyword_type="product", pages=2)
        
        if not df_product.empty:
            print(f"수집된 상품 키워드: {len(df_product)}개")
            print("상위 5개 키워드:")
            print(df_product.head(5))
            print(f"상품 키워드 저장 완료: {filename}")
        else:
            print("상품 키워드를 찾지 못했습니다.")
        
        # 예제 3: 데이터랩에서 키워드 직접 수집
        print("\n[예제 3] 데이터랩 인기 키워드 직접 수집")
        keywords, category = collector.collect_datalab_keywords(pages=2)
        
        if keywords:
            print(f"데이터랩에서 {len(keywords)}개의 키워드 수집됨")
            print(f"카테고리: {category}")
            print("상위 10개 키워드:")
            for i, kw in enumerate(keywords[:10], 1):
                print(f"{i}. {kw}")
        else:
            print("데이터랩에서 키워드를 찾지 못했습니다.")
    
    finally:
        # 키워드 수집기 종료
        collector.close()
        print("\n키워드 수집기를 종료했습니다.")

if __name__ == "__main__":
    # 비동기 메인 함수 실행
    asyncio.run(main()) 