"""
블로그 생성 워크플로우

이 모듈은 완전한 블로그 포스트를 생성하기 위한 워크플로우를 제공합니다.
"""
import copy
from typing import Dict, Any, Tuple, List, TypedDict, Annotated
from langgraph.graph import END, StateGraph

from src.workflows.graphs.search_workflow import create_search_workflow
from src.workflows.states.blog_state import BlogState, SectionState, BlogSection
from src.workflows.nodes.planners.section_planner import plan_sections
from src.workflows.nodes.writers.section_writer import write_final_sections
from src.workflows.nodes.writers.section_combiner import combine_blog_sections
from src.common.config import Configuration


def set_up_section_state(state: BlogState) -> Dict[str, Any]:
    """연구 섹션을 위한 초기 상태를 설정합니다.
    
    이 함수는:
    1. 연구가 필요한 첫 번째 섹션을 가져옵니다
    2. 섹션 상태를 초기화합니다
    
    Args:
        state: 현재 블로그 상태
        
    Returns:
        초기화된 섹션 상태
    """
    # Take the first section from research needed sections
    section = state["research_needed_sections"][0]
    
    # Prepare section state for search workflow
    section_state = SectionState(
        topic=state["topic"],
        section=section,
        search_queries=[],
        search_results=[],
        source_str="",
        search_iterations=0,
        completed_sections=[]
    )
    
    # Return section state dictionary
    return {"section_state": section_state}


def update_blog_state(state: BlogState, section_result: Dict[str, Any]) -> Dict[str, Any]:
    """완료된 섹션으로 블로그 상태를 업데이트합니다.
    
    이 함수는:
    1. 완료된 섹션을 추출합니다
    2. 연구가 필요한 섹션 목록에서 섹션을 제거합니다
    3. 완료된 섹션을 블로그 상태에 추가합니다
    
    Args:
        state: 현재 블로그 상태
        section_result: 검색 워크플로우의 결과
        
    Returns:
        업데이트된 블로그 상태
    """
    # Get completed section
    completed_sections = section_result["section_state"]["completed_sections"]
    
    # Check if any sections were completed
    if not completed_sections:
        return {}
    
    # Get remaining research needed sections
    remaining_sections = copy.deepcopy(state["research_needed_sections"])
    remaining_sections.pop(0)  # Remove the completed section
    
    # Get all completed sections so far and add the new ones
    result_sections = state["completed_sections"] + completed_sections
    
    # Return updated state
    return {
        "completed_sections": result_sections,
        "research_needed_sections": remaining_sections
    }


def get_remaining_non_research_sections(state: BlogState) -> Dict[str, Any]:
    """연구가 필요하지 않은 남은 섹션을 식별합니다.
    
    이 함수는:
    1. 모든 섹션을 가져옵니다
    2. 이미 완료된 섹션을 확인합니다
    3. 결론, 요약 등과 같은 연구가 필요하지 않은 섹션을 식별합니다
    
    Args:
        state: 현재 블로그 상태
        
    Returns:
        섹션 상태가 포함된 딕셔너리
    """
    # Get all sections and completed sections
    all_sections = state["sections"]
    completed_sections = state["completed_sections"]
    
    # Get section names that have already been completed
    completed_section_names = [section.name for section in completed_sections]
    
    # Find sections that haven't been completed yet
    remaining_sections = [section for section in all_sections if section.name not in completed_section_names]
    
    # Filter for non-research sections (결론, 요약, 서론 등)
    non_research_sections = [section for section in remaining_sections if 
                            any(keyword in section.name.lower() for keyword in ['결론', '요약', '서론', '소개'])]
    
    # Return empty dict if no non-research sections remain
    if not non_research_sections:
        return {}
    
    # Format completed sections as string for context
    section_texts = []
    for section in completed_sections:
        section_texts.append(f"### {section.name}\n{section.content}")
    blog_sections_str = "\n\n".join(section_texts)
    
    # Return the section to write and context
    return {
        "section": non_research_sections[0],
        "blog_sections_from_research": blog_sections_str
    }


def create_blog_workflow() -> StateGraph:
    """블로그 생성 워크플로우를 생성합니다.
    
    워크플로우는 다음과 같은 단계로 구성됩니다:
    1. 블로그 섹션 계획 수립
    2. 각 섹션에 대한 정보 검색 및 작성
    3. 연구가 필요하지 않은 섹션 작성 (결론 등)
    4. 모든 섹션을 결합하여 최종 블로그 생성
    
    Returns:
        블로그 생성 워크플로우 그래프
    """
    # Create the search workflow
    search_workflow = create_search_workflow()
    
    # Create the main workflow
    workflow = StateGraph(BlogState)
    
    # Add nodes
    workflow.add_node("plan_sections", plan_sections)
    workflow.add_node("set_up_section_state", set_up_section_state)
    workflow.add_node("search_section", search_workflow)
    workflow.add_node("update_blog_state", update_blog_state)
    workflow.add_node("get_remaining_non_research_sections", get_remaining_non_research_sections)
    workflow.add_node("write_final_sections", write_final_sections)
    workflow.add_node("combine_blog_sections", combine_blog_sections)
    
    # Set entry point
    workflow.set_entry_point("plan_sections")
    
    # Define main research and writing loop
    workflow.add_edge("plan_sections", "set_up_section_state")
    workflow.add_edge("set_up_section_state", "search_section")
    workflow.add_edge("search_section", "update_blog_state")
    
    # Add conditional edges for research sections
    workflow.add_conditional_edges(
        "update_blog_state",
        lambda state, result: (
            "set_up_section_state" if state["research_needed_sections"][1:] else "get_remaining_non_research_sections"
        )
    )
    
    # Add conditional edges for non-research sections
    workflow.add_conditional_edges(
        "get_remaining_non_research_sections",
        lambda state, result: (
            "write_final_sections" if result else "combine_blog_sections"
        )
    )
    
    workflow.add_edge("write_final_sections", "update_blog_state")
    workflow.add_edge("combine_blog_sections", END)
    
    # Compile workflow
    return workflow.compile() 