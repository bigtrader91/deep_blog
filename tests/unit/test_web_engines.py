"""
웹 검색 엔진 모듈 테스트
"""
import os
import sys
import unittest
import asyncio
import json
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Python 경로에 추가됨: {project_root}")

# 웹 검색 엔진 클래스 임포트
from src.core.search.engines.web_engines import PerplexitySearcher, ExaSearcher, TavilySearcher

class TestWebSearchEngines(unittest.TestCase):
    """웹 검색 엔진 관련 테스트 클래스"""
    
    def setUp(self):
        """테스트 전 환경 설정"""
        # API 키 환경 변수 저장
        self.perplexity_api_key = os.environ.get('PERPLEXITY_API_KEY', 'dummy_perplexity_key')
        self.exa_api_key = os.environ.get('EXA_API_KEY', 'dummy_exa_key')
        self.tavily_api_key = os.environ.get('TAVILY_API_KEY', 'dummy_tavily_key')
        
        # 테스트를 위한 환경 변수 설정
        os.environ['PERPLEXITY_API_KEY'] = self.perplexity_api_key
        os.environ['EXA_API_KEY'] = self.exa_api_key
        os.environ['TAVILY_API_KEY'] = self.tavily_api_key
        
        # 테스트 결과 저장 디렉토리
        self.test_output_dir = os.path.join(project_root, 'tests', 'output')
        os.makedirs(self.test_output_dir, exist_ok=True)
    
    def tearDown(self):
        """테스트 후 정리"""
        pass
    
    def save_results_to_file(self, results, prefix, is_multiple=False):
        """테스트 결과를 JSON 파일로 저장합니다.
        
        Args:
            results: 저장할 검색 결과 (리스트 또는 딕셔너리)
            prefix (str): 파일명 접두어
            is_multiple (bool): 여러 쿼리 결과인지 여부
        """
        if not results:
            return None
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.test_output_dir, f"{prefix}_{timestamp}.json")
        
        try:
            # 직렬화 가능한 형태로 변환
            if is_multiple:
                serializable_results = []
                for query_result in results:
                    serializable_query_result = {
                        'query': query_result['query'],
                        'results': []
                    }
                    for item in query_result.get('results', []):
                        serializable_item = {k: str(v) if k in ['raw_content', 'content'] and v else v 
                                            for k, v in item.items()}
                        serializable_query_result['results'].append(serializable_item)
                    
                    if 'error' in query_result:
                        serializable_query_result['error'] = query_result['error']
                        
                    serializable_results.append(serializable_query_result)
            else:
                serializable_results = []
                for item in results:
                    serializable_item = {k: str(v) if k in ['raw_content', 'content'] and v else v 
                                        for k, v in item.items()}
                    serializable_results.append(serializable_item)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2)
            
            print(f"검색 결과 저장: {filename}")
            return filename
        except Exception as e:
            print(f"결과 저장 중 오류 발생: {str(e)}")
            return None

    def test_perplexity_search_real(self):
        """PerplexitySearcher의 실제 API 호출 테스트"""
        if not os.environ.get('PERPLEXITY_API_KEY'):
            self.skipTest("PERPLEXITY_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        searcher = PerplexitySearcher()
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(searcher.search("artificial intelligence latest technology"))
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        
        # 결과 저장
        self.save_results_to_file(results, "perplexity_real_test")
    
    def test_exa_search_real(self):
        """ExaSearcher의 실제 API 호출 테스트"""
        if not os.environ.get('EXA_API_KEY'):
            self.skipTest("EXA_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        searcher = ExaSearcher(
            max_characters=1000000,  # 매우 큰 값으로 설정하여 전체 내용 가져오기
            num_results=3,  # 3개의 결과만 가져오기
            subpages=5  # 하위 페이지도 검색에 포함
        )
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(searcher.search("history of artificial intelligence development"))
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        
        # 결과 저장
        self.save_results_to_file(results, "exa_real_test")
    
    def test_tavily_search_real(self):
        """TavilySearcher의 실제 API 호출 테스트"""
        if not os.environ.get('TAVILY_API_KEY'):
            self.skipTest("TAVILY_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        searcher = TavilySearcher(
            max_results=3,  # 3개의 결과만 가져오기
            include_raw_content=True  # 전체 문서 내용 포함
        )
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(searcher.search("ethics in artificial intelligence"))
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        
        # 결과 저장
        self.save_results_to_file(results, "tavily_real_test")
    
    def test_perplexity_search_all_real(self):
        """PerplexitySearcher의 search_all 메소드 실제 API 호출 테스트"""
        if not os.environ.get('PERPLEXITY_API_KEY'):
            self.skipTest("PERPLEXITY_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        searcher = PerplexitySearcher()
        loop = asyncio.get_event_loop()
        queries = ["artificial intelligence latest technology", "machine learning algorithms"]
        results = loop.run_until_complete(searcher.search_all(queries))
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)  # 2개의 쿼리에 대한 결과
        
        # 결과 저장
        self.save_results_to_file(results, "perplexity_all_real_test", is_multiple=True)
    
    def test_exa_search_all_real(self):
        """ExaSearcher의 search_all 메소드 실제 API 호출 테스트"""
        if not os.environ.get('EXA_API_KEY'):
            self.skipTest("EXA_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        searcher = ExaSearcher(
            max_characters=1000000,  # 매우 큰 값으로 설정하여 전체 내용 가져오기
            num_results=3,  # 3개의 결과만 가져오기
            subpages=5  # 하위 페이지도 검색에 포함
        )
        loop = asyncio.get_event_loop()
        queries = ["history of artificial intelligence development", "introduction to machine learning"]
        results = loop.run_until_complete(searcher.search_all(queries))
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)  # 2개의 쿼리에 대한 결과
        
        # 결과 저장
        self.save_results_to_file(results, "exa_all_real_test", is_multiple=True)
    
    def test_tavily_search_all_real(self):
        """TavilySearcher의 search_all 메소드 실제 API 호출 테스트"""
        if not os.environ.get('TAVILY_API_KEY'):
            self.skipTest("TAVILY_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        searcher = TavilySearcher(
            max_results=3,  # 3개의 결과만 가져오기
            include_raw_content=True  # 전체 문서 내용 포함
        )
        loop = asyncio.get_event_loop()
        queries = ["ethics in artificial intelligence", "deep learning technology"]
        results = loop.run_until_complete(searcher.search_all(queries))
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)  # 2개의 쿼리에 대한 결과
        
        # 결과 저장
        self.save_results_to_file(results, "tavily_all_real_test", is_multiple=True)

if __name__ == "__main__":
    unittest.main() 