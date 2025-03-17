"""
공급자 관리 유틸리티

이 모듈은 API 키 관리 및 환경 변수 처리를 위한 유틸리티 함수를 제공합니다.
"""
import os
from typing import Any, Dict, Optional, Literal
import logging
from dataclasses import dataclass, field
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 로깅 설정
logger = logging.getLogger(__name__)

# 환경 변수 매핑
ENV_VARS = {
    # LLM 제공자
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    
    # 검색 엔진
    "tavily": "TAVILY_API_KEY",
    "perplexity": "PERPLEXITY_API_KEY",
    "exa": "EXA_API_KEY",
    "serper": "SERPER_API_KEY",
    
    # 학술 검색
    "pubmed": "PUBMED_API_KEY",
    "arxiv": "ARXIV_API_KEY",
}

# LLM 제공자 유형
LLMProvider = Literal["openai", "anthropic"]

# 설정 캐시
_CONFIG_CACHE: Dict[str, Any] = {}

@dataclass
class PlannerProvider:
    """섹션 계획 생성기 제공자 설정"""
    provider: LLMProvider = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7

@dataclass
class WriterProvider:
    """콘텐츠 작성 제공자 설정"""
    provider: LLMProvider = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7

@dataclass
class ProviderConfiguration:
    """API 공급자 설정
    
    이 클래스는 다양한 API 공급자에 대한 설정을 관리합니다.
    """
    # 섹션 계획 생성 설정
    planner: PlannerProvider = field(default_factory=PlannerProvider)
    
    # 콘텐츠 작성 설정
    writer: WriterProvider = field(default_factory=WriterProvider)
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """특정 공급자의 API 키를 가져옵니다.
        
        Args:
            provider: 공급자 이름
            
        Returns:
            API 키 문자열 또는 None (키가 없는 경우)
        """
        return get_config_value(provider)

def get_env_var(var_name: str) -> Optional[str]:
    """환경 변수 값을 가져옵니다.
    
    Args:
        var_name: 환경 변수 이름
        
    Returns:
        환경 변수 값 또는 None (존재하지 않는 경우)
    """
    value = os.environ.get(var_name)
    if not value:
        logger.warning(f"환경 변수 '{var_name}'를 찾을 수 없습니다.")
    return value


def get_config_value(key: str) -> Optional[str]:
    """API 키 또는 구성값을 가져옵니다.
    
    이 함수는 다음과 같은 순서로 값을 조회합니다:
    1. 캐시된 값 확인
    2. 환경 변수에서 직접 조회
    3. 매핑된 환경 변수 이름을 통해 조회
    
    Args:
        key: 구성 키 이름
        
    Returns:
        구성 값 또는 None (존재하지 않는 경우)
    """
    # 캐시된 값 확인
    if key in _CONFIG_CACHE:
        return _CONFIG_CACHE[key]
    
    # 직접적인 환경 변수 확인
    value = get_env_var(key)
    if value:
        _CONFIG_CACHE[key] = value
        return value
    
    # 매핑된 환경 변수 이름 확인
    if key in ENV_VARS:
        value = get_env_var(ENV_VARS[key])
        if value:
            _CONFIG_CACHE[key] = value
            return value
    
    return None


def set_config_value(key: str, value: str) -> None:
    """구성 값을 설정합니다.
    
    Args:
        key: 구성 키 이름
        value: 구성 값
    """
    _CONFIG_CACHE[key] = value
    logger.debug(f"구성 값 설정: {key}")


def clear_config_cache() -> None:
    """구성 캐시를 초기화합니다."""
    _CONFIG_CACHE.clear()
    logger.debug("구성 캐시 초기화 완료") 