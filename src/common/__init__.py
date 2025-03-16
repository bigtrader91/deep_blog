"""
base.py: 설정 기본 클래스 및 공통 유틸리티
blog.py: 블로그 구조, 템플릿 관련 설정
search.py: 검색 API 관련 설정
providers.py: AI 제공자(OpenAI, Anthropic 등) 관련 설정
constants.py: 템플릿, 기본값 등 상수 정의

"""

from dataclasses import dataclass
from src.common.config.base import BaseConfiguration
from src.common.config.blog import BlogConfiguration
from src.common.config.search import SearchConfiguration, SearchAPI
from src.common.config.providers import ProviderConfiguration, PlannerProvider, WriterProvider

@dataclass(kw_only=True)
class Configuration(BlogConfiguration, SearchConfiguration, ProviderConfiguration):
    """전체 애플리케이션 설정을 통합하는 클래스"""
    pass

__all__ = [
    'Configuration',
    'SearchAPI',
    'PlannerProvider',
    'WriterProvider',
]