"""
검색 엔진 모듈 테스트
"""
import os
import sys
import unittest
from unittest import mock
import asyncio
import json
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Python 경로에 추가됨: {project_root}")

# dotenv.load_dotenv 모킹 설정
with mock.patch('dotenv.load_dotenv'):
    from src.core.search.engines.naver import NaverCrawler
from src.core.search.engines.google import GoogleNews

class TestSearchEngines(unittest.TestCase):
    """검색 엔진 관련 테스트 클래스"""
    
    def setUp(self):
        """테스트 전 환경 설정"""
        # 네이버 API 키 설정 (테스트용)
        self.naver_client_id = os.environ.get('NAVER_CLIENT_ID')
        self.naver_client_secret = os.environ.get('NAVER_CLIENT_SECRET')
        
        # 테스트 결과 저장 디렉토리
        self.test_output_dir = os.path.join(project_root, 'tests', 'output')
        os.makedirs(self.test_output_dir, exist_ok=True)
    
    def tearDown(self):
        """테스트 후 정리"""
        pass

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_naver_init_missing_env_vars(self):
        """NaverCrawler 초기화 테스트 - 환경 변수 없음"""
        # 환경 변수가 없을 때 ValueError가 발생해야 함
        with self.assertRaises(ValueError):
            _ = NaverCrawler(skip_env_load=True)
    
    def test_naver_init_with_params(self):
        """NaverCrawler 초기화 테스트 - 파라미터 제공"""
        # 파라미터로 API 키 제공 시 정상 초기화
        crawler = NaverCrawler(client_id="test_id", client_secret="test_secret", skip_env_load=True)
        self.assertEqual(crawler.client_id, "test_id")
        self.assertEqual(crawler.client_secret, "test_secret")
    
    def test_google_news_init(self):
        """GoogleNews 초기화 테스트"""
        news = GoogleNews()
        self.assertIsNotNone(news)
    
    @unittest.skipIf(not os.environ.get('NAVER_CLIENT_ID') or not os.environ.get('NAVER_CLIENT_SECRET'),
                   "네이버 API 키가 환경 변수에 설정되어 있지 않습니다")
    def test_naver_search_news(self):
        """네이버 뉴스 검색 테스트"""
        crawler = NaverCrawler()
        
        # 실제 검색 실행
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(crawler.search_news("인공지능", display=3))
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIn('items', results)
        self.assertIsInstance(results['items'], list)
        
        # 결과 저장 (선택적)
        if results['items']:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(self.test_output_dir, f"naver_news_test_{timestamp}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"네이버 뉴스 검색 결과 저장: {filename}")
    
    @unittest.skipIf(not os.environ.get('NAVER_CLIENT_ID') or not os.environ.get('NAVER_CLIENT_SECRET'),
                   "네이버 API 키가 환경 변수에 설정되어 있지 않습니다")
    def test_naver_crawl_all(self):
        """네이버 통합 검색 테스트"""
        crawler = NaverCrawler()
        
        # 실제 검색 실행
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(crawler.crawl_all("인공지능", display=2, max_total_results=6))
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIn('news', results)
        self.assertIn('encyc', results)
        self.assertIn('kin', results)
        
        # 결과 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = crawler.save_results(results, os.path.join(self.test_output_dir, f"naver_all_test_{timestamp}.json"))
        print(f"네이버 통합 검색 결과 저장: {filename}")
    
    def test_google_news_search(self):
        """구글 뉴스 검색 테스트"""
        news = GoogleNews()
        
        # 실제 검색 실행
        results = news.search_by_keyword("인공지능", max_results=3)
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        
        # 결과 저장 (선택적)
        if results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(self.test_output_dir, f"google_news_test_{timestamp}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"구글 뉴스 검색 결과 저장: {filename}")
    
    def test_google_news_search_all(self):
        """구글 뉴스 상세 검색 테스트"""
        news = GoogleNews()
        
        # 실제 검색 실행
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(news.search_all("인공지능", max_results=2))
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        
        # 결과 저장
        if results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = news.save_results(results, os.path.join(self.test_output_dir, f"google_news_all_test_{timestamp}.json"))
            print(f"구글 뉴스 상세 검색 결과 저장: {filename}")

if __name__ == "__main__":
    unittest.main()