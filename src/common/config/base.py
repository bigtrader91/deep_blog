"""기본 설정 클래스 및 유틸리티를 정의합니다."""

from dataclasses import dataclass, fields
from typing import Any, Optional, Dict, TypeVar, Type
from langchain_core.runnables import RunnableConfig
import os

T = TypeVar('T')

@dataclass
class BaseConfiguration:
    """모든 설정 클래스의 기본이 되는 클래스입니다."""
    
    @classmethod
    def from_runnable_config(
        cls: Type[T],
        config: Optional[RunnableConfig] = None
    ) -> T:
        """RunnableConfig에서 Configuration 인스턴스를 생성합니다.
        
        Args:
            config: Langchain의 RunnableConfig 객체
            
        Returns:
            생성된 설정 인스턴스
        """
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v is not None})
