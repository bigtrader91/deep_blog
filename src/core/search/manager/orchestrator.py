"""
검색 엔진 오케스트레이션을 위한 매니저 클래스

이 모듈은 다양한 검색 엔진을 통합하여 관리하고 실행하는 기능을 제공합니다.
"""
import os
import asyncio
from typing import List, Dict, Any, Optional, Union

from langsmith import traceable

from src.core.search.formatters.source_formatter import SourceFormatter
from src.common.logging import get_logger

# 로거 설정
logger = get_logger(__name__)


class SearchOrchestrator:
    """검색 엔진 오케스트레이션을 위한 클래스
    
    이 클래스는 다양한 검색 엔진을 통합적으로 관리하고,
    각 검색 엔진의 특성에 맞는 파라미터를 처리하여 검색을 실행합니다.
    """
    
    # 지원되는 검색 엔진 목록
    SUPPORTED_ENGINES = {
        "tavily", "perplexity", "exa", "arxiv", "pubmed", "linkup", "data_crawler"
    }
    
    # 검색 API별 허용 매개변수 정의
    SEARCH_API_PARAMS = {
        "exa": ["max_characters", "num_results", "include_domains", "exclude_domains", "subpages"],
        "tavily": ["max_results", "include_raw_content", "topic"],
        "perplexity": ["model"],
        "arxiv": ["load_max_docs", "get_full_documents", "load_all_available_meta"],
        "pubmed": ["top_k_results", "email", "api_key", "doc_content_chars_max"],
        "linkup": ["depth"],
        "data_crawler": ["display", "include_google", "max_content_length", "max_results"],
    }
    
    def __init__(self):
        """SearchOrchestrator 초기화"""
        pass
    
    @staticmethod
    def get_search_params(search_api: str, search_api_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        지정된 검색 API에서 허용하는 매개변수만 포함하도록 search_api_config 딕셔너리를 필터링합니다.

        Args:
            search_api (str): 검색 API 식별자(예: "exa", "tavily").
            search_api_config (Optional[Dict[str, Any]]): 검색 API 구성 딕셔너리.

        Returns:
            Dict[str, Any]: 검색 함수에 전달할 매개변수 딕셔너리.
        """
        # 허용된 매개변수 목록 가져오기
        accepted_params = SearchOrchestrator.SEARCH_API_PARAMS.get(search_api, [])

        # 구성이 제공되지 않은 경우 빈 딕셔너리 반환
        if not search_api_config:
            return {}

        # 허용된 매개변수만 포함하도록 구성 필터링
        return {k: v for k, v in search_api_config.items() if k in accepted_params}
    
    @traceable
    async def select_and_execute_search(self, search_api: str, query_list: List[str], 
                                        params_to_pass: Optional[Dict[str, Any]] = None,
                                        format_results: bool = True,
                                        max_tokens_per_source: int = 4000,
                                        include_raw_content: bool = True) -> Union[str, List[Dict[str, Any]]]:
        """적절한 검색 API를 선택하고 실행합니다.
        
        Args:
            search_api: 사용할 검색 API 이름
            query_list: 실행할 검색 쿼리 목록
            params_to_pass: 검색 API에 전달할 매개변수
            format_results: 결과를 형식화된 문자열로 반환할지 여부 
            max_tokens_per_source: 소스당 최대 토큰 수 (format_results가 True인 경우에만 사용)
            include_raw_content: 원본 콘텐츠를 포함할지 여부 (format_results가 True인 경우에만 사용)
            
        Returns:
            형식화된 문자열 또는 검색 결과 목록
            
        Raises:
            ValueError: 지원되지 않는 검색 API가 지정된 경우
        """
        # 파라미터가 None이면 빈 딕셔너리로 초기화
        if params_to_pass is None:
            params_to_pass = {}
            
        if search_api not in self.SUPPORTED_ENGINES:
            raise ValueError(f"지원되지 않는 검색 API: {search_api}")
        
        logger.info(f"검색 엔진 '{search_api}' 실행 중: 쿼리 {len(query_list)}개")
        
        # 검색 엔진별 실행 로직
        search_results = None
        
        if search_api == "tavily":
            # 현재 모듈에서 직접 import하여 사용
            from src.core.search.engines.web_engines import TavilySearcher
            searcher = TavilySearcher(api_key=os.getenv("TAVILY_API_KEY"))
            search_results = await self._execute_search_all(searcher, query_list, params_to_pass)
            
        elif search_api == "perplexity":
            from src.core.search.engines.web_engines import PerplexitySearcher
            searcher = PerplexitySearcher(api_key=os.getenv("PERPLEXITY_API_KEY"))
            search_results = self._execute_search_all_sync(searcher, query_list, params_to_pass)
            
        elif search_api == "exa":
            from src.core.search.engines.web_engines import ExaSearcher
            searcher = ExaSearcher(api_key=os.getenv("EXA_API_KEY"))
            search_results = await self._execute_search_all(searcher, query_list, params_to_pass)
            
        elif search_api == "arxiv":
            from src.core.search.engines.academic import ArxivSearcher
            searcher = ArxivSearcher()
            search_results = await self._execute_search_all(searcher, query_list, params_to_pass)
            
        elif search_api == "pubmed":
            from src.core.search.engines.academic import PubMedSearcher
            searcher = PubMedSearcher(email=params_to_pass.get("email"), api_key=params_to_pass.get("api_key"))
            search_results = await self._execute_search_all(searcher, query_list, params_to_pass)
            
        elif search_api == "linkup":
            # LinkupSearcher는 현재 구현되어 있지 않으므로 예외 발생
            raise NotImplementedError("LinkupSearcher는 아직 구현되지 않았습니다.")
            
        elif search_api == "data_crawler":
            # DataCrawlerSearcher는 현재 구현되어 있지 않으므로 예외 발생
            raise NotImplementedError("DataCrawlerSearcher는 아직 구현되지 않았습니다.")
        
        # 결과 형식화
        if format_results and search_results:
            return SourceFormatter.deduplicate_and_format_sources(
                search_results, 
                max_tokens_per_source=max_tokens_per_source,
                include_raw_content=include_raw_content
            )
        
        return search_results
    
    async def _execute_search_all(self, searcher, query_list: List[str], params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """비동기 검색 엔진의 search_all 메서드를 실행합니다.
        
        Args:
            searcher: 검색 엔진 인스턴스
            query_list: 쿼리 목록
            params: 검색 매개변수
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        try:
            # 검색 엔진에 따라 search_all 또는 다른 메서드 호출
            if hasattr(searcher, 'search_all'):
                return await searcher.search_all(query_list, **params)
            else:
                # 검색 엔진에 search_all이 없는 경우 개별 검색 실행
                results = []
                for query in query_list:
                    # search 메서드가 딕셔너리를 반환하는지 또는 리스트를 반환하는지에 따라 다르게 처리
                    result = await searcher.search(query, **params)
                    
                    # search 메서드가 딕셔너리를 반환하는 경우
                    if isinstance(result, dict):
                        results.append(result)
                    # search 메서드가 리스트를 반환하는 경우
                    elif isinstance(result, list):
                        # 각 결과를 query 키와 함께 딕셔너리로 변환
                        results.append({
                            'query': query,
                            'results': result
                        })
                        
                return results
        except Exception as e:
            logger.error(f"검색 실행 중 오류 발생: {str(e)}")
            # 오류가 발생한 경우 빈 결과와 오류 메시지 반환
            return [{
                'query': query,
                'results': [],
                'error': str(e)
            } for query in query_list]
    
    def _execute_search_all_sync(self, searcher, query_list: List[str], params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """동기 검색 엔진의 search_all 메서드를 실행합니다.
        
        Args:
            searcher: 검색 엔진 인스턴스
            query_list: 쿼리 목록
            params: 검색 매개변수
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        try:
            # 검색 엔진에 따라 search_all 또는 다른 메서드 호출
            if hasattr(searcher, 'search_all'):
                return searcher.search_all(query_list, **params)
            else:
                # 검색 엔진에 search_all이 없는 경우 개별 검색 실행
                results = []
                for query in query_list:
                    result = searcher.search(query, **params)
                    
                    # search 메서드가 딕셔너리를 반환하는 경우
                    if isinstance(result, dict):
                        results.append(result)
                    # search 메서드가 리스트를 반환하는 경우
                    elif isinstance(result, list):
                        # 각 결과를 query 키와 함께 딕셔너리로 변환
                        results.append({
                            'query': query,
                            'results': result
                        })
                        
                return results
        except Exception as e:
            logger.error(f"검색 실행 중 오류 발생: {str(e)}")
            # 오류가 발생한 경우 빈 결과와 오류 메시지 반환
            return [{
                'query': query,
                'results': [],
                'error': str(e)
            } for query in query_list]
