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
    planner_provider = get_config_value(configurable.planner_provider)
    planner_model_name = get_config_value(configurable.planner_model)
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


async def _search_tavily(query: str, api_key: str) -> Dict[str, Any]:
    """Tavily 검색 API를 사용하여 웹 검색을 수행합니다.
    
    Args:
        query: 검색 쿼리
        api_key: Tavily API 키
        
    Returns:
        검색 결과 사전
    """
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    data = {
        "query": query,
        "search_depth": "advanced",
        "include_domains": [],
        "exclude_domains": [],
        "max_results": 5
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.tavily.com/search",
            headers=headers,
            json=data
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result
            else:
                error_text = await response.text()
                logger.error(f"Tavily 검색 오류: {error_text}")
                return {"results": []}


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
    search_provider = get_config_value(configurable.searcher_provider)
    search_api_key = get_config_value(configurable.searcher_api_key)
    
    if not search_api_key:
        logger.error(f"{search_provider} API 키를 찾을 수 없습니다.")
        return {"search_results": []}
    
    # Perform search for each query
    logger.info(f"{len(search_queries)}개의 쿼리로 {search_provider} 검색을 수행합니다...")
    
    all_results = []
    
    # Currently only support Tavily
    if search_provider == "tavily":
        search_tasks = [_search_tavily(query, search_api_key) for query in search_queries]
        tavily_results = await asyncio.gather(*search_tasks)
        
        # Process Tavily results
        for query, result in zip(search_queries, tavily_results):
            if "results" in result:
                for item in result["results"]:
                    all_results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", ""),
                        "score": item.get("score", 0),
                        "source_type": "tavily",
                        "query": query,
                        "metadata": {
                            "crawled_at": datetime.now().isoformat()
                        }
                    })
    else:
        logger.warning(f"지원되지 않는 검색 제공자: {search_provider}")
    
    logger.info(f"총 {len(all_results)}개의 검색 결과를 찾았습니다.")
    
    return {"search_results": all_results} 