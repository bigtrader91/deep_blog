"""
프롬프트 모듈

이 패키지는 블로그 생성 워크플로우에서 사용되는 다양한 프롬프트 템플릿을 제공합니다.
"""

# 모듈 가져오기
from .planning import section_planner_instructions
from .search import search_query_generator_instructions
from .writing import (
    section_writer_instructions,
    section_writer_inputs,
    final_section_writer_instructions
)
from .evaluation import section_grader_instructions
from .editing import combine_sections_instructions

# 프롬프트 모두 가져오기 
__all__ = [
    # 계획 관련 프롬프트
    'section_planner_instructions',
    
    # 검색 관련 프롬프트
    'search_query_generator_instructions',
    
    # 작성 관련 프롬프트
    'section_writer_instructions',
    'section_writer_inputs', 
    'final_section_writer_instructions',
    
    # 평가 관련 프롬프트
    'section_grader_instructions',
    
    # 편집 관련 프롬프트
    'combine_sections_instructions'
]
