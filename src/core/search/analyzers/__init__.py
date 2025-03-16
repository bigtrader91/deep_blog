"""
검색 모듈의 통합 인터페이스를 제공합니다.

이 모듈은 다양한 검색 엔진들을 통합하여 사용할 수 있는 인터페이스를 제공합니다.
"""

from src.core.search.engines.naver import NaverCrawler
from src.core.search.engines.google import GoogleNews

__all__ = ['NaverCrawler', 'GoogleNews'] 