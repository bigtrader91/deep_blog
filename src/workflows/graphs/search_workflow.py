"""
검색 워크플로우

이 모듈은 블로그 섹션 작성에 필요한 정보를 검색하기 위한 워크플로우를 제공합니다.
"""
from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph import END, StateGraph

from src.workflows.states.blog_state import SectionState
from src.workflows.nodes.searchers.section_searcher import generate_queries, search_web
from src.workflows.nodes.processors.source_combiner import combine_search_results
from src.workflows.nodes.writers.section_writer import write_section
from src.common.config import Configuration


def create_search_workflow() -> StateGraph:
    """블로그 섹션 작성을 위한 검색 워크플로우를 생성합니다.
    
    워크플로우는 다음과 같은 단계로 구성됩니다:
    1. 검색 쿼리 생성
    2. 생성된 쿼리로 웹 검색 수행
    3. 검색 결과 결합
    4. 결합된 결과로 섹션 작성 
    5. 품질이 충분하면 완료, 그렇지 않으면 추가 검색 수행
    
    Returns:
        검색 워크플로우 그래프
    """
    # Create workflow graph
    workflow = StateGraph(SectionState)
    
    # Add nodes
    workflow.add_node("generate_queries", generate_queries)
    workflow.add_node("search_web", search_web)
    workflow.add_node("combine_search_results", combine_search_results)
    workflow.add_node("write_section", write_section)
    
    # Define workflow
    workflow.set_entry_point("generate_queries")
    workflow.add_edge("generate_queries", "search_web")
    workflow.add_edge("search_web", "combine_search_results")
    workflow.add_edge("combine_search_results", "write_section")
    workflow.add_conditional_edges(
        "write_section",
        lambda state, result: result["goto"] if "goto" in result else END
    )
    
    # Compile workflow
    return workflow.compile() 