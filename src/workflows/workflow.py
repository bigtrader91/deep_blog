"""
워크플로우 인터페이스

이 모듈은 블로그 생성 시스템의 주요 워크플로우 인터페이스를 제공합니다.
"""
import asyncio
from typing import Dict, Any

from langchain_core.runnables import RunnableConfig

from src.workflows.graphs.blog_workflow import create_blog_workflow
from src.workflows.states.blog_state import BlogState
from src.common.config import Configuration


async def generate_blog(topic: str, config: Dict[str, Any] = None) -> str:
    """블로그 주제에 대한 완전한 블로그 포스트를 생성합니다.
    
    이 함수는:
    1. 블로그 워크플로우를 생성합니다
    2. 주제에 대한 초기 블로그 상태를 설정합니다
    3. 워크플로우를 실행하여 블로그를 생성합니다
    
    Args:
        topic: 블로그 주제
        config: 워크플로우 구성 옵션
        
    Returns:
        생성된 블로그 콘텐츠
    """
    # Create blog workflow
    workflow = create_blog_workflow()
    
    # Set up initial state
    initial_state = BlogState(
        topic=topic,
        sections=[],
        research_needed_sections=[],
        completed_sections=[],
        blog_post=""
    )
    
    # Prepare config
    runnable_config = RunnableConfig(configurable=config or {})
    
    # Run the workflow asynchronously
    final_state = await workflow.ainvoke(initial_state, config=runnable_config)
    
    # Return the blog post from the final state
    return final_state["blog_post"] 