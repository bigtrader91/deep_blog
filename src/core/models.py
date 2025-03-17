"""
모델 초기화 및 관리 유틸리티

이 모듈은 언어 모델 초기화 및 구성을 위한 기능을 제공합니다.
"""
from typing import Dict, Any, Optional, Union

def init_chat_model(
    model: str,
    model_provider: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    thinking: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Any:
    """채팅 모델을 초기화합니다.
    
    Args:
        model: 모델 이름
        model_provider: 모델 제공자 (openai, anthropic 등)
        temperature: 생성 온도 (기본값: 0.7)
        max_tokens: 최대 토큰 수
        thinking: 사고 과정을 위한 설정 
        **kwargs: 기타 모델별 매개변수
        
    Returns:
        초기화된 채팅 모델
    """
    # 실제 모델 초기화는 langchain.chat_models에서 처리
    from langchain.chat_models import ChatOpenAI, ChatAnthropic
    
    # 모델 제공자에 따라 다른 모델 초기화
    if model_provider.lower() == "openai":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    elif model_provider.lower() == "anthropic":
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    else:
        raise ValueError(f"지원되지 않는 모델 제공자: {model_provider}") 