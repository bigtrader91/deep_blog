"""
공통 상태 모델

이 모듈은 워크플로우에서 사용되는 공통 상태 모델과 타입을 정의합니다.
"""

from typing import Annotated, List, TypedDict, Literal
from pydantic import BaseModel, Field
import operator

class Section(BaseModel):
    """블로그 섹션 모델"""
    name: str = Field(
        description="Name for this section of the blog.",
    )
    description: str = Field(
        description="Brief overview of the main topics and concepts to be covered in this section.",
    )
    research: bool = Field(
        description="Whether to perform web research for this section of the blog."
    )
    content: str = Field(
        description="The content of the section."
    )   

class Sections(BaseModel):
    """블로그 섹션 목록 모델"""
    sections: List[Section] = Field(
        description="Sections of the blog.",
    )

class SearchQuery(BaseModel):
    """검색 쿼리 모델"""
    search_query: str = Field(None, description="Query for web search.")

class Queries(BaseModel):
    """검색 쿼리 목록 모델"""
    queries: List[SearchQuery] = Field(
        description="List of search queries.",
    )

class Feedback(BaseModel):
    """섹션 평가 피드백 모델"""
    grade: Literal["pass","fail"] = Field(
        description="Evaluation result indicating whether the response meets requirements ('pass') or needs revision ('fail')."
    )
    follow_up_queries: List[SearchQuery] = Field(
        description="List of follow-up search queries.",
    )

class blogStateInput(TypedDict):
    """블로그 상태 입력"""
    topic: str # blog topic
    
class blogStateOutput(TypedDict):
    """블로그 상태 출력"""
    final_blog: str # Final blog

class blogState(TypedDict):
    """블로그 상태"""
    topic: str # blog topic    
    feedback_on_blog_plan: str # Feedback on the blog plan
    sections: list[Section] # List of blog sections 
    completed_sections: Annotated[list, operator.add] # Send() API key
    blog_sections_from_research: str # String of any completed sections from research to write final sections
    final_blog: str # Final blog

class SectionState(TypedDict):
    """섹션 상태"""
    topic: str # blog topic
    section: Section # blog section  
    search_iterations: int # Number of search iterations done
    search_queries: list[SearchQuery] # List of search queries
    source_str: str # String of formatted source content from web search
    blog_sections_from_research: str # String of any completed sections from research to write final sections
    completed_sections: list[Section] # Final key we duplicate in outer state for Send() API

class SectionOutputState(TypedDict):
    """섹션 출력 상태"""
    completed_sections: list[Section] # Final key we duplicate in outer state for Send() API 