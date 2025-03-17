"""
학술 검색 엔진 모듈 테스트
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

# 학술 검색 엔진 클래스 임포트
from src.core.search.engines.academic import ArxivSearcher, PubMedSearcher

class TestAcademicSearchEngines(unittest.TestCase):
    """학술 검색 엔진 관련 테스트 클래스"""
    
    def setUp(self):
        """테스트 전 환경 설정"""
        # PubMed 테스트를 위한 환경 변수 설정
        self.pubmed_email = os.environ.get('PUBMED_EMAIL', 'test@example.com')
        self.pubmed_api_key = os.environ.get('PUBMED_API_KEY', '')
        
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
                        serializable_item = {k: str(v) if k == 'raw_content' and v else v 
                                            for k, v in item.items()}
                        serializable_query_result['results'].append(serializable_item)
                    
                    if 'error' in query_result:
                        serializable_query_result['error'] = query_result['error']
                        
                    serializable_results.append(serializable_query_result)
            else:
                serializable_results = []
                for item in results:
                    serializable_item = {k: str(v) if k == 'raw_content' and v else v 
                                        for k, v in item.items()}
                    serializable_results.append(serializable_item)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2)
            
            print(f"검색 결과 저장: {filename}")
            return filename
        except Exception as e:
            print(f"결과 저장 중 오류 발생: {str(e)}")
            return None

    def test_arxiv_searcher_init(self):
        """ArxivSearcher 초기화 테스트"""
        # 기본 설정으로 초기화
        searcher = ArxivSearcher()
        self.assertEqual(searcher.load_max_docs, 5)
        self.assertTrue(searcher.get_full_documents)
        self.assertTrue(searcher.load_all_available_meta)
        
        # 사용자 지정 설정으로 초기화
        custom_searcher = ArxivSearcher(
            load_max_docs=3,
            get_full_documents=True,
            load_all_available_meta=True
        )
        self.assertEqual(custom_searcher.load_max_docs, 3)
        self.assertTrue(custom_searcher.get_full_documents)
        self.assertTrue(custom_searcher.load_all_available_meta)
    
    def test_pubmed_searcher_init(self):
        """PubMedSearcher 초기화 테스트"""
        # 기본 설정으로 초기화
        searcher = PubMedSearcher()
        self.assertEqual(searcher.top_k_results, 5)
        
        # 사용자 지정 설정으로 초기화
        custom_searcher = PubMedSearcher(
            top_k_results=3,
            doc_content_chars_max=1000000,  # 매우 큰 값으로 설정하여 전체 내용 가져오기
            email='custom@example.com',
            api_key='test_api_key'
        )
        self.assertEqual(custom_searcher.top_k_results, 3)
        self.assertEqual(custom_searcher.doc_content_chars_max, 1000000)
        self.assertEqual(custom_searcher.email, 'custom@example.com')
        self.assertEqual(custom_searcher.api_key, 'test_api_key')
    
    def test_arxiv_search_real(self):
        """ArxivSearcher의 실제 API 호출 테스트"""
        searcher = ArxivSearcher(
            load_max_docs=3,  # 3개의 문서만 가져오기
            get_full_documents=True,  # 전체 문서 내용 가져오기
            load_all_available_meta=True  # 모든 메타데이터 가져오기
        )
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(searcher.search("artificial intelligence"))
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        
        # 결과 저장
        self.save_results_to_file(results, "arxiv_real_test")
    
    def test_pubmed_search_real(self):
        """PubMedSearcher의 실제 API 호출 테스트"""
        searcher = PubMedSearcher(
            top_k_results=3,  # 3개의 결과만 가져오기
            doc_content_chars_max=1000000,  # 매우 큰 값으로 설정하여 전체 내용 가져오기
            email=self.pubmed_email
        )
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(searcher.search("medical artificial intelligence"))
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        
        # 결과 저장
        self.save_results_to_file(results, "pubmed_real_test")
    
    def test_arxiv_search_all_real(self):
        """ArxivSearcher의 search_all 메소드 실제 API 호출 테스트"""
        searcher = ArxivSearcher(
            load_max_docs=3,  # 3개의 문서만 가져오기
            get_full_documents=True,  # 전체 문서 내용 가져오기
            load_all_available_meta=True  # 모든 메타데이터 가져오기
        )
        loop = asyncio.get_event_loop()
        queries = ["artificial intelligence", "machine learning"]
        results = loop.run_until_complete(searcher.search_all(queries))
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)  # 2개의 쿼리에 대한 결과
        
        # 결과 저장
        self.save_results_to_file(results, "arxiv_all_real_test", is_multiple=True)
    
    def test_pubmed_search_all_real(self):
        """PubMedSearcher의 search_all 메소드 실제 API 호출 테스트"""
        searcher = PubMedSearcher(
            top_k_results=3,  # 3개의 결과만 가져오기
            doc_content_chars_max=1000000,  # 매우 큰 값으로 설정하여 전체 내용 가져오기
            email=self.pubmed_email
        )
        loop = asyncio.get_event_loop()
        queries = ["medical artificial intelligence", "coronavirus"]
        results = loop.run_until_complete(searcher.search_all(queries))
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)  # 2개의 쿼리에 대한 결과
        
        # 결과 저장
        self.save_results_to_file(results, "pubmed_all_real_test", is_multiple=True)

if __name__ == "__main__":
    unittest.main() 