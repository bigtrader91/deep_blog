"""
블로그 상태 모듈

이 모듈은 블로그 생성 워크플로우의 상태를 표현하는 클래스를 제공합니다.
"""
from typing import List, Dict, Any, Optional, TypedDict, Union
from dataclasses import dataclass, field
from pydantic import BaseModel


class BlogSection(BaseModel):
    """블로그 섹션 모델
    
    블로그의 각 섹션을 표현하는 모델입니다.
    
    Attributes:
        name: 섹션 이름/제목
        description: 섹션 내용 설명
        content: 작성된 섹션 콘텐츠
    """
    name: str
    description: str
    content: str = ""

    class Config:
        """Pydantic 구성"""
        from_attributes = True


class Feedback(BaseModel):
    """섹션 피드백 모델
    
    생성된 섹션에 대한 피드백과 추가 쿼리를 표현하는 모델입니다.
    
    Attributes:
        grade: 평가 결과 (pass/fail)
        feedback: 상세 피드백
        follow_up_queries: 추가 정보를 찾기 위한 쿼리 목록
    """
    grade: str  # "pass" or "fail"
    feedback: str
    follow_up_queries: List[str] = []


class BlogState(TypedDict):
    """블로그 생성 워크플로우 상태
    
    전체 블로그 생성 워크플로우의 상태를 표현합니다.
    
    Attributes:
        topic: 블로그 주제
        sections: 계획된 모든 섹션 목록
        research_needed_sections: 연구가 필요한 섹션 목록
        completed_sections: 작성 완료된 섹션 목록
        blog_post: 최종 블로그 콘텐츠
    """
    topic: str
    sections: List[BlogSection]
    research_needed_sections: List[BlogSection]
    completed_sections: List[BlogSection]
    blog_post: str


class SectionState(TypedDict):
    """섹션 작성 워크플로우 상태
    
    개별 섹션 작성 워크플로우의 상태를 표현합니다.
    
    Attributes:
        topic: 블로그 주제
        section: 현재 작성 중인 섹션
        search_queries: 생성된 검색 쿼리 목록
        search_results: 검색 결과 목록
        source_str: 결합된 검색 결과 문자열
        search_iterations: 수행된 검색 반복 횟수
        completed_sections: 완료된 섹션 목록
        blog_sections_from_research: 연구된 섹션을 기반으로 작성할 때 사용할 컨텍스트
    """
    topic: str
    section: BlogSection
    search_queries: List[str]
    search_results: List[Dict[str, Any]]
    source_str: str
    search_iterations: int
    completed_sections: List[BlogSection]
    blog_sections_from_research: Optional[str] = None
