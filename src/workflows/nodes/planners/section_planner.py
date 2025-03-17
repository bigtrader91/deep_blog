"""
섹션 계획 노드

이 모듈은 블로그 주제에 대한 섹션 계획을 생성하는 노드를 제공합니다.
"""
from typing import List
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.workflows.states.blog_state import BlogSection, BlogState
from src.prompts import section_planner_instructions
from src.common.config import Configuration
from src.common.config.providers import get_config_value


def plan_sections(state: BlogState, config: RunnableConfig) -> dict:
    """블로그 주제를 위한 섹션 계획을 생성합니다.
    
    이 노드는:
    1. 블로그 주제를 입력으로 받습니다
    2. 블로그 주제를 다루기 위한 섹션 목록을 생성합니다
    3. 각 섹션에 대해 자세한 설명을 제공합니다
    
    Args:
        state: 블로그 주제를 포함하는 현재 상태
        config: 섹션 계획을 위한 구성
        
    Returns:
        계획된 섹션 목록이 포함된 딕셔너리
    """
    # Get state
    topic = state["topic"]
    
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    
    # Prepare prompt for section planning
    system_instructions = section_planner_instructions.format(topic=topic, num_sections=configurable.number_of_blog_sections)
    
    # Generate section plan using planner model
    planner_provider = configurable.planner_provider
    planner_model_name = configurable.planner_model
    planner_model = init_chat_model(model=planner_model_name, model_provider=planner_provider, temperature=0)
    
    # Get section plan and convert to correct type
    response = planner_model.invoke([SystemMessage(content=system_instructions),
                                    HumanMessage(content=f"Plan sections for a blog post about '{topic}'.")])
    
    # 응답을 파싱하여 BlogSection 객체 목록으로 변환
    section_text = response.content
    section_list = []
    
    # 응답 텍스트에서 섹션 정보 추출
    import re
    sections = re.split(r'\n\s*\d+\.\s+', section_text)
    sections = [s for s in sections if s.strip()]  # 빈 섹션 제거
    
    for section_content in sections:
        lines = section_content.strip().split('\n')
        if not lines:
            continue
            
        # 첫 번째 줄을 섹션 이름으로 사용
        name = lines[0].strip()
        # 나머지 줄을 설명으로 사용
        description = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
        
        # BlogSection 객체 생성
        section = BlogSection(name=name, description=description)
        section_list.append(section)
    
    # Return the updated state
    return {"sections": section_list, "research_needed_sections": section_list} 