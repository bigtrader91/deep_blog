"""
검색 결과를 형식화하기 위한 유틸리티 클래스

이 모듈은 다양한 검색 소스의 결과를 가공하고 형식화하는 기능을 제공합니다.
"""
from typing import List, Dict, Any, Optional, Union


class SourceFormatter:
    """검색 결과를 형식화하는 유틸리티 클래스
    
    이 클래스는 다양한 검색 엔진에서 반환된 결과를 일관된 형식으로 가공하고,
    중복을 제거하여 사용하기 쉽게 변환합니다.
    """
    
    @classmethod
    def deduplicate_and_format_sources(cls, search_response: List[Dict[str, Any]], 
                                      max_tokens_per_source: int = 4000, 
                                      include_raw_content: bool = True) -> str:
        """
        검색 응답 리스트를 가져와 읽기 쉬운 문자열로 형식화합니다.
        원본 콘텐츠(raw_content)를 약 max_tokens_per_source 토큰으로 제한합니다.
     
        Args:
            search_response: 검색 응답 딕셔너리 리스트, 각 응답은 다음을 포함합니다:
                - query: str
                - results: 다음 필드를 가진 딕셔너리 리스트:
                    - title: str
                    - url: str
                    - content: str
                    - score: float
                    - raw_content: str|None
            max_tokens_per_source: 소스당 최대 토큰 수
            include_raw_content: 원본 콘텐츠 포함 여부
                
        Returns:
            str: 중복이 제거된 소스가 포함된 형식화된 문자열
        """
        # 모든 결과 수집
        sources_list = []
        for response in search_response:
            sources_list.extend(response['results'])
        
        # URL 기준으로 중복 제거
        unique_sources = {source['url']: source for source in sources_list}

        # 출력 형식화
        formatted_text = "소스 콘텐츠:\n"
        for i, source in enumerate(unique_sources.values(), 1):
            formatted_text += f"{'='*80}\n"  # 명확한 섹션 구분자
            formatted_text += f"소스: {source['title']}\n"
            formatted_text += f"{'-'*80}\n"  # 하위 섹션 구분자
            formatted_text += f"URL: {source['url']}\n===\n"
            formatted_text += f"소스의 가장 관련성 높은 내용: {source['content']}\n===\n"
            if include_raw_content:
                # 토큰당 약 4자로 대략 추정
                char_limit = max_tokens_per_source * 4
                # None인 raw_content 처리
                raw_content = source.get('raw_content', '')
                if raw_content is None:
                    raw_content = ''
                    print(f"경고: {source['url']} 소스에 raw_content가 없습니다")
                if len(raw_content) > char_limit:
                    raw_content = raw_content[:char_limit] + "... [잘림]"
                formatted_text += f"{max_tokens_per_source} 토큰으로 제한된 전체 소스 내용: {raw_content}\n\n"
            formatted_text += f"{'='*80}\n\n"  # 섹션 종료 구분자
                    
        return formatted_text.strip()
    
    @classmethod
    def merge_search_results(cls, results_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """여러 검색 결과를 병합하고 중복을 제거합니다.
        
        Args:
            results_list: 여러 검색 엔진의 결과 목록
            
        Returns:
            List[Dict[str, Any]]: 중복이 제거된 통합 검색 결과
        """
        merged_results = []
        
        # 모든 결과를 하나의 리스트로 통합
        for results in results_list:
            merged_results.extend(results)
        
        # URL 기준으로 중복 제거 (최신 또는 더 높은 점수의 결과 유지)
        unique_results = {}
        for result in merged_results:
            url = result.get('url', '')
            if not url:
                # URL이 없는 경우 무시
                continue
                
            # 이미 URL이 있는 경우, 점수가 더 높은 결과로 업데이트
            if url in unique_results:
                if result.get('score', 0) > unique_results[url].get('score', 0):
                    unique_results[url] = result
            else:
                unique_results[url] = result
        
        return list(unique_results.values())
    
    @classmethod
    def extract_key_information(cls, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """검색 결과에서 핵심 정보를 추출합니다.
        
        Args:
            search_results: 검색 결과 목록
            
        Returns:
            Dict[str, Any]: 주요 주제, 핵심 포인트, 중요 소스 등의 요약 정보
        """
        if not search_results:
            return {
                'main_topics': [],
                'key_points': [],
                'top_sources': []
            }
        
        # 점수 기준으로 정렬
        sorted_results = sorted(search_results, key=lambda x: x.get('score', 0), reverse=True)
        
        # 상위 소스 추출
        top_sources = [
            {
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'source_type': result.get('source_type', '')
            }
            for result in sorted_results[:5]  # 상위 5개 소스만
        ]
        
        # 여기에서는 간단한 예시만 제공하며, 실제로는 NLP 등을 사용하여 
        # 더 정교한 주제 추출 및 요약을 구현할 수 있습니다.
        
        return {
            'main_topics': [],  # NLP로 추출 가능
            'key_points': [],   # 텍스트 요약으로 추출 가능
            'top_sources': top_sources
        }
