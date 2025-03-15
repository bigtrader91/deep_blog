"""
네이버 크롤러 테스트 스크립트

네이버 크롤러를 테스트하고 결과를 확인하는 스크립트입니다.
사용법: python test_data_crawler.py <검색어> [결과 개수]
"""
import os
import sys
import asyncio
import json
from pprint import pprint

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_crawler import NaverCrawler, main


async def test_data_crawler(query: str, display: int = 3) -> None:
    """네이버 크롤러 테스트 함수
    
    Args:
        query (str): 검색어
        display (int, optional): 각 소스별 검색 결과 개수. 기본값은 3.
    """
    print(f"네이버 크롤러 테스트를 시작합니다. 검색어: {query}, 결과 개수: {display}")
    
    # 크롤러 초기화
    crawler = NaverCrawler()
    
    # 1. 뉴스 검색 테스트
    print("\n===== 뉴스 검색 테스트 =====")
    news_results = await crawler.search_news(query, display)
    print(f"뉴스 검색 결과: {len(news_results.get('items', []))}건")
    if news_results.get('items'):
        print("첫 번째 뉴스 제목:", news_results['items'][0]['title'])
    
    # 2. 백과사전 검색 테스트
    print("\n===== 백과사전 검색 테스트 =====")
    encyc_results = await crawler.search_encyc(query, display)
    print(f"백과사전 검색 결과: {len(encyc_results.get('items', []))}건")
    if encyc_results.get('items'):
        print("첫 번째 백과사전 제목:", encyc_results['items'][0]['title'])
    
    # 3. 지식인 검색 테스트
    print("\n===== 지식인 검색 테스트 =====")
    kin_results = await crawler.search_kin(query, display)
    print(f"지식인 검색 결과: {len(kin_results.get('items', []))}건")
    if kin_results.get('items'):
        print("첫 번째 지식인 제목:", kin_results['items'][0]['title'])
    
    # 4. 상세 내용 가져오기 테스트
    if news_results.get('items'):
        print("\n===== 상세 내용 가져오기 테스트 =====")
        first_news = news_results['items'][0]
        print(f"뉴스 URL: {first_news['link']}")
        
        processed_news = await crawler.process_news_content(first_news)
        print(f"상세 내용 크기: {len(processed_news['content'])} 바이트")
        print("내용 일부:", processed_news['content'][:200] + "..." if len(processed_news['content']) > 200 else processed_news['content'])
    
    # 5. 병렬 크롤링 테스트
    print("\n===== 병렬 크롤링 테스트 =====")
    results = await crawler.crawl_all(query, display)
    print("병렬 크롤링 결과:")
    print(f"뉴스: {len(results['news'])}건")
    print(f"백과사전: {len(results['encyc'])}건")
    print(f"지식인: {len(results['kin'])}건")
    
    # 6. 결과 저장 테스트
    print("\n===== 결과 저장 테스트 =====")
    filename = crawler.save_results(results, f"naver_search_test_{query}.json")
    print(f"결과가 {filename}에 저장되었습니다.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        display = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        asyncio.run(test_data_crawler(query, display))
    else:
        print("사용법: python test_data_crawler.py <검색어> [결과 개수]")
        print("예시: python test_data_crawler.py \"인공지능\" 3") 