"""
섹션 결합 노드

이 모듈은 작성된 섹션들을 묶어 최종 블로그 포스트를 생성하는 노드를 제공합니다.
"""
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.common.config import Configuration
from src.common.config.providers import get_config_value
from src.workflows.states.blog_state import BlogState
from src.prompts import combine_sections_instructions


def combine_blog_sections(state: BlogState, config: RunnableConfig) -> dict:
    """완성된 섹션들을 결합하여 최종 블로그 포스트를 생성합니다.
    
    이 노드는:
    1. 완성된 모든 섹션을 가져옵니다
    2. 블로그 주제와 관련된 일관된 단일 블로그 포스트로 결합합니다
    3. 최종 블로그 콘텐츠를 반환합니다
    
    Args:
        state: 완성된 모든 섹션이 들어있는 현재 상태
        config: 결합 모델에 대한 구성
        
    Returns:
        완성된 블로그 콘텐츠가 포함된 딕셔너리
    """
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    
    # Get state 
    topic = state["topic"]
    sections = state["completed_sections"]
    
    # Prepare sections 
    formatted_sections = []
    for section in sections:
        formatted_sections.append(f"### {section.name}\n{section.content}")
    
    sections_str = "\n\n".join(formatted_sections)
    
    # Prepare prompt 
    system_instructions = combine_sections_instructions.format(topic=topic, sections=sections_str)
    
    # Generate final blog post
    writer_provider = get_config_value(configurable.writer_provider)
    writer_model_name = get_config_value(configurable.writer_model)
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, temperature=0) 
    
    blog_post = writer_model.invoke([SystemMessage(content=system_instructions),
                                    HumanMessage(content=f"Combine these sections into a cohesive blog post about {topic}.")])
    
    # Return the combined blog post
    return {"blog_post": blog_post.content} 