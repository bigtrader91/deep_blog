"""
웹 검색을 위한 전문 검색 엔진들을 제공합니다.

이 모듈은 Perplexity, Exa, Tavily 등 다양한 웹 검색 API를 활용한 검색 클래스를 제공합니다.
"""

import asyncio
import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

from exa_py import Exa
from tavily import AsyncTavilyClient

from src.common.logging import get_logger

# 로거 설정
logger = get_logger(__name__)

class PerplexitySearcher:
    """Perplexity API를 활용한 웹 검색기

    이 클래스는 Perplexity API를 통해 웹 검색을 수행합니다.
    """
    
    def __init__(self, api_key: Optional[str] = None) -> None:
        """PerplexitySearcher 초기화
        
        Args:
            api_key (Optional[str], optional): Perplexity API 키. 기본값은 환경변수에서 로드.
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY가 필요합니다.")
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Perplexity API를 사용하여 검색을 수행합니다.
        
        Args:
            query (str): 검색 쿼리
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        try:
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": "sonar-pro",
                "messages": [
                    {
                        "role": "system",
                        "content": "Search the web and provide factual information with sources."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ]
            }
            
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            # 응답 파싱
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            citations = data.get("citations", ["https://perplexity.ai"])
            
            # 결과 목록 생성
            results = []
            current_time = datetime.now().isoformat()
            
            # 첫 번째 인용은 전체 내용을 얻음
            results.append({
                "title": f"Perplexity 검색, 소스 1",
                "url": citations[0],
                "content": content,
                "raw_content": content,
                "score": 1.0,
                "source_type": "perplexity",
                "metadata": {
                    "model": "sonar-pro",
                    "query": query,
                    "crawled_at": current_time
                }
            })
            
            # 추가 인용 추가 (내용 중복 없이)
            for i, citation in enumerate(citations[1:], start=2):
                results.append({
                    "title": f"Perplexity 검색, 소스 {i}",
                    "url": citation,
                    "content": "주요 소스 참고",
                    "raw_content": None,
                    "score": 0.5,
                    "source_type": "perplexity",
                    "metadata": {
                        "reference_number": i,
                        "crawled_at": current_time
                    }
                })
            
            logger.info(f"Perplexity 검색 완료: '{query}', {len(results)}개 결과 발견")
            return results
            
        except Exception as e:
            logger.error(f"Perplexity 검색 중 오류 발생: {str(e)}")
            return []
    
    async def search_all(self, queries: List[str]) -> List[Dict[str, Any]]:
        """여러 쿼리에 대해 검색을 수행합니다.
        
        Args:
            queries (List[str]): 검색 쿼리 목록
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        all_results = []
        
        for i, query in enumerate(queries):
            # API 속도 제한 준수 (1초 간격)
            if i > 0:
                await asyncio.sleep(1.0)
            
            try:
                results = await self.search(query)
                all_results.append({
                    'query': query,
                    'results': results
                })
            except Exception as e:
                logger.error(f"검색 쿼리 '{query}' 처리 중 오류 발생: {str(e)}")
                all_results.append({
                    'query': query,
                    'results': [],
                    'error': str(e)
                })
        
        return all_results


class ExaSearcher:
    """Exa API를 활용한 웹 검색기

    이 클래스는 Exa API를 통해 웹 검색을 수행합니다.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 max_characters: Optional[int] = None,
                 num_results: int = 5,
                 include_domains: Optional[List[str]] = None,
                 exclude_domains: Optional[List[str]] = None,
                 subpages: Optional[int] = None) -> None:
        """ExaSearcher 초기화
        
        Args:
            api_key (Optional[str], optional): Exa API 키. 기본값은 환경변수에서 로드.
            max_characters (Optional[int], optional): 각 결과의 원본 내용 최대 문자 수.
            num_results (int, optional): 쿼리당 결과 수. 기본값은 5.
            include_domains (Optional[List[str]], optional): 포함할 도메인 목록.
            exclude_domains (Optional[List[str]], optional): 제외할 도메인 목록.
            subpages (Optional[int], optional): 결과당 가져올 하위 페이지 수.
        """
        self.api_key = api_key or os.getenv("EXA_API_KEY")
        if not self.api_key:
            raise ValueError("EXA_API_KEY가 필요합니다.")
        
        # include_domains와 exclude_domains 둘 다 지정되면 에러
        if include_domains and exclude_domains:
            raise ValueError("include_domains와 exclude_domains를 동시에 지정할 수 없습니다.")
        
        self.max_characters = max_characters
        self.num_results = num_results
        self.include_domains = include_domains
        self.exclude_domains = exclude_domains
        self.subpages = subpages
        
        # Exa 클라이언트 초기화
        self.exa = Exa(api_key=self.api_key)
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Exa API를 사용하여 검색을 수행합니다.
        
        Args:
            query (str): 검색 쿼리
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        try:
            # 비동기 컨텍스트에서 동기 함수 실행
            loop = asyncio.get_event_loop()
            
            # 검색 함수 정의
            def exa_search_fn():
                # 파라미터 딕셔너리 구성
                kwargs = {
                    "text": True if self.max_characters is None else {"max_characters": self.max_characters},
                    "summary": True,
                    "num_results": self.num_results
                }
                
                # 선택적 파라미터 추가
                if self.subpages is not None:
                    kwargs["subpages"] = self.subpages
                    
                if self.include_domains:
                    kwargs["include_domains"] = self.include_domains
                elif self.exclude_domains:
                    kwargs["exclude_domains"] = self.exclude_domains
                    
                return self.exa.search_and_contents(query, **kwargs)
            
            # 쓰레드 풀에서 동기 검색 실행
            response = await loop.run_in_executor(None, exa_search_fn)
            
            # 결과 형식화
            formatted_results = []
            seen_urls = set()  # 중복 URL 추적
            current_time = datetime.now().isoformat()
            
            # 값 안전하게 가져오는 헬퍼 함수
            def get_value(item, key, default=None):
                if isinstance(item, dict):
                    return item.get(key, default)
                else:
                    return getattr(item, key, default) if hasattr(item, key) else default
            
            # 결과 목록 가져오기
            results_list = get_value(response, 'results', [])
            
            # 모든 주요 결과 처리
            for result in results_list:
                # 기본값 0.0으로 점수 가져오기
                score = get_value(result, 'score', 0.0)
                
                # 텍스트와 요약 결합
                text_content = get_value(result, 'text', '')
                summary_content = get_value(result, 'summary', '')
                
                content = text_content
                if summary_content:
                    if content:
                        content = f"{summary_content}\n\n{content}"
                    else:
                        content = summary_content
                
                title = get_value(result, 'title', '')
                url = get_value(result, 'url', '')
                
                # 이미 본 URL 건너뛰기 (중복 항목 제거)
                if url in seen_urls:
                    continue
                    
                seen_urls.add(url)
                
                # 메인 결과 항목
                result_entry = {
                    "title": title,
                    "url": url,
                    "content": content,
                    "raw_content": text_content,
                    "score": score,
                    "source_type": "exa",
                    "metadata": {
                        "summary": summary_content,
                        "query": query,
                        "crawled_at": current_time
                    }
                }
                
                # 포맷된 결과에 추가
                formatted_results.append(result_entry)
            
            # subpage 파라미터가 제공된 경우에만 하위 페이지 처리
            if self.subpages is not None:
                for result in results_list:
                    subpages_list = get_value(result, 'subpages', [])
                    for subpage in subpages_list:
                        # 하위 페이지 점수 가져오기
                        subpage_score = get_value(subpage, 'score', 0.0)
                        
                        # 하위 페이지 내용 결합
                        subpage_text = get_value(subpage, 'text', '')
                        subpage_summary = get_value(subpage, 'summary', '')
                        
                        subpage_content = subpage_text
                        if subpage_summary:
                            if subpage_content:
                                subpage_content = f"{subpage_summary}\n\n{subpage_content}"
                            else:
                                subpage_content = subpage_summary
                        
                        subpage_url = get_value(subpage, 'url', '')
                        subpage_title = get_value(subpage, 'title', '')
                        
                        # 이미 본 URL 건너뛰기
                        if subpage_url in seen_urls:
                            continue
                            
                        seen_urls.add(subpage_url)
                        
                        formatted_results.append({
                            "title": subpage_title,
                            "url": subpage_url,
                            "content": subpage_content,
                            "raw_content": subpage_text,
                            "score": subpage_score,
                            "source_type": "exa",
                            "metadata": {
                                "summary": subpage_summary,
                                "is_subpage": True,
                                "parent_url": get_value(result, 'url', ''),
                                "query": query,
                                "crawled_at": current_time
                            }
                        })
            
            logger.info(f"Exa 검색 완료: '{query}', {len(formatted_results)}개 결과 발견")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Exa 검색 중 오류 발생: {str(e)}")
            return []
    
    async def search_all(self, queries: List[str]) -> List[Dict[str, Any]]:
        """여러 쿼리에 대해 검색을 수행합니다.
        
        Args:
            queries (List[str]): 검색 쿼리 목록
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        all_results = []
        
        for i, query in enumerate(queries):
            # API 속도 제한 준수 (0.25초 간격)
            if i > 0:
                await asyncio.sleep(0.25)
            
            try:
                results = await self.search(query)
                all_results.append({
                    'query': query,
                    'results': results
                })
            except Exception as e:
                logger.error(f"검색 쿼리 '{query}' 처리 중 오류 발생: {str(e)}")
                all_results.append({
                    'query': query,
                    'results': [],
                    'error': str(e)
                })
                
                # 429 에러시 추가 딜레이 적용
                if "429" in str(e):
                    logger.warning("속도 제한 초과. 추가 딜레이 적용...")
                    await asyncio.sleep(1.0)
        
        return all_results


class TavilySearcher:
    """Tavily API를 활용한 웹 검색기

    이 클래스는 Tavily API를 통해 웹 검색을 수행합니다.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 max_results: int = 5,
                 include_raw_content: bool = True,
                 topic: str = "general") -> None:
        """TavilySearcher 초기화
        
        Args:
            api_key (Optional[str], optional): Tavily API 키. 기본값은 환경변수에서 로드.
            max_results (int, optional): 최대 결과 수. 기본값은 5.
            include_raw_content (bool, optional): 원본 콘텐츠 포함 여부. 기본값은 True.
            topic (str, optional): 검색 주제. 기본값은 "general".
        """
        self.api_key = api_key
        self.max_results = max_results
        self.include_raw_content = include_raw_content
        self.topic = topic
        
        # AsyncTavilyClient 초기화 (API 키는 환경변수에서 자동으로 로드됨)
        self.client = AsyncTavilyClient(api_key=self.api_key)
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Tavily API를 사용하여 검색을 수행합니다.
        
        Args:
            query (str): 검색 쿼리
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        try:
            response = await self.client.search(
                query,
                max_results=self.max_results,
                include_raw_content=self.include_raw_content,
                topic=self.topic
            )
            
            # 응답 포맷 변환
            results = response.get('results', [])
            formatted_results = []
            current_time = datetime.now().isoformat()
            
            for result in results:
                # 통일된 형식으로 변환
                formatted_result = {
                    "title": result.get('title', ''),
                    "url": result.get('url', ''),
                    "content": result.get('content', ''),
                    "raw_content": result.get('raw_content', ''),
                    "score": result.get('score', 0.0),
                    "source_type": "tavily",
                    "metadata": {
                        "topic": self.topic,
                        "query": query,
                        "crawled_at": current_time
                    }
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"Tavily 검색 완료: '{query}', {len(formatted_results)}개 결과 발견")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Tavily 검색 중 오류 발생: {str(e)}")
            return []
    
    async def search_all(self, queries: List[str]) -> List[Dict[str, Any]]:
        """여러 쿼리에 대해 검색을 수행합니다.
        
        Args:
            queries (List[str]): 검색 쿼리 목록
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        search_tasks = []
        for query in queries:
            search_tasks.append(self.search(query))
        
        # 모든 검색 동시 실행
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        all_results = []
        for i, (query, result) in enumerate(zip(queries, results)):
            if isinstance(result, Exception):
                logger.error(f"검색 쿼리 '{query}' 처리 중 오류 발생: {str(result)}")
                all_results.append({
                    'query': query,
                    'results': [],
                    'error': str(result)
                })
            else:
                all_results.append({
                    'query': query,
                    'results': result
                })
        
        return all_results 