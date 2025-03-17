"""검색 관련 설정을 정의합니다."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from .base import BaseConfiguration

class SearchAPI(Enum):
    """사용 가능한 검색 API 목록"""
    PERPLEXITY = "perplexity"
    TAVILY = "tavily"
    EXA = "exa"
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    LINKUP = "linkup"

@dataclass(kw_only=True)
class SearchConfiguration(BaseConfiguration):
    """검색 관련 설정"""
    
    search_api: SearchAPI = SearchAPI.TAVILY
    search_api_config: Optional[Dict[str, Any]] = None
    number_of_queries: int = 5  # 반복당 생성할 검색 쿼리 수
    max_search_depth: int = 5  # 최대 반성 + 검색 반복 횟수
