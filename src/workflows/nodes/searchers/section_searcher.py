"""
섹션 검색 노드

이 모듈은 블로그 섹션 작성에 필요한 정보를 검색하는 노드를 제공합니다.
"""
import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
import aiohttp
from datetime import datetime

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.common.config import Configuration
from src.common.config.providers import get_config_value
from src.common.config.search import SearchAPI
from src.core.search.manager.orchestrator import create_searcher, multi_search
from src.workflows.states.blog_state import SectionState
from src.prompts import search_query_generator_instructions

# 로깅 설정
logger = logging.getLogger(__name__)


def generate_queries(state: SectionState, config: RunnableConfig) -> Dict[str, Any]:
    """섹션 주제에 대한 검색 쿼리를 생성합니다.
    
    이 노드는:
    1. 섹션 주제와 설명을 가져옵니다
    2. 언어 모델을 사용하여 관련 검색 쿼리를 생성합니다
    3. 생성된 쿼리를 반환합니다
    
    Args:
        state: 섹션 정보가 포함된 현재 상태
        config: 쿼리 생성 구성 (쿼리 수 등)
        
    Returns:
        생성된 검색 쿼리가 포함된 딕셔너리
    """
    # 디버깅을 위해 state 딕셔너리 내용 출력
    logger.info(f"generate_queries 함수의 state 딕셔너리: {state}")
    
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    
    # Get section info
    topic = state["topic"]
    section = state["section"]
    
    # Check if queries already exist
    if state["search_queries"]:
        logger.info(f"이미 존재하는 쿼리를 사용합니다: {len(state['search_queries'])}개")
        return {"search_queries": state["search_queries"]}
    
    # Format prompt for query generation
    system_instructions = search_query_generator_instructions.format(
        topic=topic,
        section_topic=section.name,
        section_description=section.description,
        num_queries=configurable.number_of_queries
    )
    
    # Generate queries using planner model
    planner_provider = configurable.planner_provider
    planner_model_name = configurable.planner_model
    planner_model = init_chat_model(model=planner_model_name, model_provider=planner_provider, temperature=0)
    
    logger.info(f"'{section.name}' 섹션에 대한 검색 쿼리 생성 중...")
    
    query_response = planner_model.invoke([
        SystemMessage(content=system_instructions),
        HumanMessage(content=f"'{section.name}' 섹션을 위한 검색 쿼리를 생성해주세요.")
    ])
    
    # Parse queries from the response
    queries = []
    for line in query_response.content.strip().split("\n"):
        clean_line = line.strip()
        if clean_line and not clean_line.startswith('#') and not clean_line.startswith('-'):
            # Remove numbering if present (e.g., "1. query" -> "query")
            if "." in clean_line and clean_line[0].isdigit():
                clean_line = clean_line.split(".", 1)[1].strip()
            queries.append(clean_line)
    
    logger.info(f"'{section.name}' 섹션에 대해 {len(queries)}개의 쿼리가 생성되었습니다.")
    
    return {"search_queries": queries}


async def search_web(state: SectionState, config: RunnableConfig) -> Dict[str, Any]:
    """웹 검색을 수행하여 섹션 작성에 필요한 정보를 수집합니다.
    
    이 노드는:
    1. 생성된 쿼리를 가져옵니다
    2. 각 쿼리에 대해 웹 검색을 수행합니다
    3. 검색 결과를 구조화된 형식으로 반환합니다
    
    Args:
        state: 검색 쿼리가 포함된 현재 상태
        config: 검색 API 구성
        
    Returns:
        검색 결과가 포함된 딕셔너리
    """
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    
    # Get search queries
    search_queries = state["search_queries"]
    if not search_queries:
        logger.warning("검색 쿼리가 없습니다.")
        return {"search_results": []}
    
    # Get API key for search
    search_provider = configurable.searcher_provider
    search_api_key = get_config_value(configurable.searcher_api_key)
    
    logger.info(f"{len(search_queries)}개의 쿼리로 {search_provider} 검색을 수행합니다...")
    
    all_results = []
    
    try:
        # 통합 검색 방식 사용 (orchestrator의 multi_search 활용)
        search_results = await multi_search(search_provider, search_queries, search_api_key)
        
        # 검색 결과 처리
        for result_set in search_results:
            query = result_set.get('query', '')
            results = result_set.get('results', [])
            
            for item in results:
                # 표준화된 결과 형식으로 변환
                formatted_result = {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0),
                    "source_type": search_provider,
                    "query": query,
                    "metadata": {
                        "crawled_at": datetime.now().isoformat()
                    }
                }
                
                # 원본 콘텐츠가 있으면 추가
                if "raw_content" in item:
                    formatted_result["raw_content"] = item["raw_content"]
                
                all_results.append(formatted_result)
    
    except Exception as e:
        logger.error(f"검색 중 오류 발생: {str(e)}")
    
    logger.info(f"총 {len(all_results)}개의 검색 결과를 찾았습니다.")
    
    return {"search_results": all_results} 