"""검색 워크플로우 모듈입니다.

이 모듈은 블로그 섹션 작성에 필요한 정보를 수집하기 위한 검색 워크플로우를 제공합니다.
워크플로우는 다음과 같은 단계로 구성됩니다:
1. 검색 쿼리 생성 (generate_queries)
2. 웹 검색 수행 (search_web)
3. 검색 결과 결합 (combine_search_results)
4. 섹션 작성 (write_section)
"""
from typing import Dict, Any, List, TypedDict, Optional, Literal, Union, cast

from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from src.workflows.nodes.processors.source_combiner import combine_search_results
from src.workflows.nodes.searchers.section_searcher import generate_queries, search_web
from src.workflows.nodes.writers.section_writer import write_section
from src.workflows.states.blog_state import BlogSection, SectionState


class SearchState(TypedDict, total=False):
    """검색 워크플로우 상태"""
    section_state: SectionState
    

def _prepare_result(fn_result: Dict[str, Any]) -> Dict[str, Any]:
    """노드 함수의 결과를 처리하여 section_state 내에 저장합니다.
    
    Args:
        fn_result: 노드 함수의 결과
    
    Returns:
        section_state가 포함된 딕셔너리
    """
    return {"section_state": fn_result}


def create_search_workflow() -> StateGraph:
    """검색 워크플로우 그래프를 생성합니다.
    
    워크플로우는 다음과 같은 단계로 구성됩니다:
    1. 검색 쿼리 생성 (generate_queries)
    2. 웹 검색 수행 (search_web)
    3. 검색 결과 결합 (combine_search_results)
    4. 섹션 작성 (write_section)
    
    Returns:
        검색 워크플로우 그래프
    """
    # 워크플로우 그래프 생성
    workflow = StateGraph(SearchState)
    
    # 노드 함수 래퍼
    def generate_queries_wrapper(state: SearchState) -> Dict[str, Any]:
        section_state = state["section_state"]
        result = generate_queries(section_state)
        return _prepare_result(result)
    
    def search_web_wrapper(state: SearchState) -> Dict[str, Any]:
        section_state = state["section_state"]
        result = search_web(section_state)
        return _prepare_result(result)
    
    def combine_search_results_wrapper(state: SearchState) -> Dict[str, Any]:
        section_state = state["section_state"]
        result = combine_search_results(section_state)
        return _prepare_result(result)
    
    def write_section_wrapper(state: SearchState) -> Dict[str, Any]:
        section_state = state["section_state"]
        result = write_section(section_state)
        return _prepare_result(result)
    
    # 노드 추가
    workflow.add_node("generate_queries", generate_queries_wrapper)
    workflow.add_node("search_web", search_web_wrapper)
    workflow.add_node("combine_search_results", combine_search_results_wrapper)
    workflow.add_node("write_section", write_section_wrapper)
    
    # 시작점 설정
    workflow.set_entry_point("generate_queries")
    
    # 가장자리 정의
    workflow.add_edge("generate_queries", "search_web")
    workflow.add_edge("search_web", "combine_search_results")
    workflow.add_edge("combine_search_results", "write_section")
    
    # 조건부 가장자리 정의
    workflow.add_conditional_edges(
        "write_section",
        lambda state, result: (
            "generate_queries" 
            if result["section_state"].get("goto") == "generate_queries" 
            else END
        )
    )
    
    # 워크플로우 컴파일
    return workflow.compile()