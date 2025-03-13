# src/configuration.py
import os
from enum import Enum
from dataclasses import dataclass, fields
from typing import Any, Optional, Dict 

from langchain_core.runnables import RunnableConfig
from dataclasses import dataclass

DEFAULT_blog_STRUCTURE = """Use the following structure to write a blog post (Answer in Korean):

1. Introduction
   - Include an engaging hook to capture reader attention.
   - Briefly introduce the blog topic (no research required).

2. Main Body Sections (Total of 7 sections)
   - Each section should focus on a sub-topic of the main topic.
   - Write at least 200 characters per section.
   - Include a table in the second and fifth sections.
   - Include a list in the third and sixth sections.
   - Include FAQ in the seventh section.
   - FAQ should be in the following format:


3. Conclusion
   - Summarize the key message from the main content naturally.
   - Emphasize key points to ensure readers remember them.
   - Provide a simple action point (something readers can actually do).
   - Add tags to the end of the blog post.
"""

class SearchAPI(Enum):
    PERPLEXITY = "perplexity"
    TAVILY = "tavily"
    EXA = "exa"
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    LINKUP = "linkup"

class PlannerProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GROQ = "groq"

class WriterProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GROQ = "groq"

@dataclass(kw_only=True)
class Configuration:
    """챗봇의 구성 가능한 필드."""
    blog_structure: str = DEFAULT_blog_STRUCTURE # 기본 보고서 구조로 기본값 설정
    number_of_queries: int = 5 # 반복당 생성할 검색 쿼리 수
    max_search_depth: int = 5 # 최대 반성 + 검색 반복 횟수
    planner_provider: PlannerProvider = PlannerProvider.OPENAI  # 제공자로 Anthropic을 기본값으로 설정
    planner_model: str = "gpt-4o-mini" # claude-3-7-sonnet-latest를 기본값으로 설정
    writer_provider: WriterProvider = WriterProvider.OPENAI # 제공자로 Anthropic을 기본값으로 설정
    writer_model: str = "gpt-4o-mini" # claude-3-5-sonnet-latest를 기본값으로 설정
    search_api: SearchAPI = SearchAPI.TAVILY # TAVILY를 기본값으로 설정
    search_api_config: Optional[Dict[str, Any]] = None 

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """RunnableConfig에서 Configuration 인스턴스를 생성합니다."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})