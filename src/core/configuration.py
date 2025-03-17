"""
모델 및 워크플로우를 위한 설정 관리

이 모듈은 Configuration 클래스를 제공하여 실행 구성을 처리합니다.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, TypeVar, Type

from langchain_core.runnables import RunnableConfig

T = TypeVar('T')

@dataclass
class Configuration:
    """모델 및 워크플로우 설정을 관리합니다."""
    
    # 모델 제공자 
    planner_provider: str = "openai"
    planner_model: str = "gpt-4"
    writer_provider: str = "openai"
    writer_model: str = "gpt-4"
    
    # 검색 설정
    searcher_provider: str = "tavily"
    searcher_api_key: str = ""
    
    # 워크플로우 설정
    number_of_blog_sections: int = 5
    number_of_queries: int = 3
    max_search_depth: int = 3
    
    @classmethod
    def from_runnable_config(cls: Type[T], config: Optional[RunnableConfig] = None) -> T:
        """RunnableConfig에서 Configuration 인스턴스를 생성합니다.
        
        Args:
            config: Langchain의 RunnableConfig 객체
            
        Returns:
            생성된 설정 인스턴스
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