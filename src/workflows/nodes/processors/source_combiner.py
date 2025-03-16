"""
소스 결합 노드

이 모듈은 검색된 소스를 결합하여 블로그 작성을 위한 컨텍스트를 준비하는 노드를 제공합니다.
"""
import json

from langchain_core.runnables import RunnableConfig

from src.workflows.states.blog_state import SectionState
from src.common.config import Configuration


def combine_search_results(state: SectionState, config: RunnableConfig) -> dict:
    """검색 결과를 결합하여 작성에 사용할 컨텍스트를 생성합니다.
    
    이 노드는:
    1. 검색 결과를 가져옵니다
    2. 결과를 JSON 형식으로 변환하여 컨텍스트로 결합합니다
    3. 컨텍스트를 반환하여 작성 노드에서 사용할 수 있게 합니다
    
    Args:
        state: 검색 결과를 포함하는 현재 상태
        config: 구성 (이 함수에서는 사용되지 않음)
        
    Returns:
        결합된 소스 문자열이 포함된 딕셔너리
    """
    # Get state
    search_results = state["search_results"]
    search_iterations = state["search_iterations"]
    
    # Increment the search iteration counter
    search_iterations += 1
    
    # Convert search results to JSON string
    if search_results:
        sources_str = json.dumps(search_results, ensure_ascii=False, indent=2)
    else:
        sources_str = "검색 결과가 없습니다."
    
    # Return the combined sources
    return {"source_str": sources_str, "search_iterations": search_iterations} 