"""
구성 모듈

이 모듈은 블로그 생성 워크플로우의 구성 설정을 제공합니다.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from langchain_core.runnables import RunnableConfig


@dataclass
class Configuration:
    """블로그 생성 워크플로우 구성
    
    이 클래스는 워크플로우 실행에 필요한 모든 구성 설정을 정의합니다.
    
    Attributes:
        planner_provider: 계획 모델 제공자
        planner_model: 계획에 사용할 모델
        writer_provider: 작성 모델 제공자
        writer_model: 콘텐츠 작성에 사용할 모델
        searcher_provider: 검색 엔진 제공자
        searcher_api_key: 검색 API 키
        number_of_blog_sections: 생성할 블로그 섹션 수
        number_of_queries: 섹션당 생성할 검색 쿼리 수
        max_search_depth: 섹션당 최대 검색 반복 횟수
    """
    planner_provider: str = "anthropic"
    planner_model: str = "claude-3-7-sonnet-latest"
    writer_provider: str = "anthropic"
    writer_model: str = "claude-3-7-sonnet-latest"
    searcher_provider: str = "tavily"
    searcher_api_key: Optional[str] = None
    number_of_blog_sections: int = 5
    number_of_queries: int = 3
    max_search_depth: int = 2
    
    @classmethod
    def from_runnable_config(cls, config: RunnableConfig) -> 'Configuration':
        """RunnableConfig에서 Configuration 인스턴스를 생성합니다.
        
        Args:
            config: LangChain RunnableConfig 객체
            
        Returns:
            구성 인스턴스
        """
        if not config or not config.get("configurable"):
            return cls()
        
        # 구성 설정 추출
        configurable = config.get("configurable", {})
        
        # 구성 인스턴스 생성
        instance = cls()
        
        # 구성 설정 적용
        for key, value in configurable.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        return instance
    
    def to_dict(self) -> Dict[str, Any]:
        """구성을 dictionary로 변환합니다.
        
        Returns:
            구성 사전
        """
        return {
            "planner_provider": self.planner_provider,
            "planner_model": self.planner_model,
            "writer_provider": self.writer_provider,
            "writer_model": self.writer_model,
            "searcher_provider": self.searcher_provider,
            "searcher_api_key": self.searcher_api_key,
            "number_of_blog_sections": self.number_of_blog_sections,
            "number_of_queries": self.number_of_queries,
            "max_search_depth": self.max_search_depth
        } 