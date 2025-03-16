"""
섹션 작성 노드

이 모듈은 블로그 섹션을 작성하고 평가하는 노드들을 제공합니다.
"""
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.constants import END
from langgraph.types import Command

from src.workflows.states.blog_state import SectionState, Feedback
from src.prompts import section_writer_instructions, section_writer_inputs, section_grader_instructions, final_section_writer_instructions
from src.common.config import Configuration
from src.common.config.providers import get_config_value


def write_section(state: SectionState, config: RunnableConfig) -> Command[Literal[END, "search_web"]]:
    """섹션을 작성하고 추가 연구가 필요한지 평가합니다.
    
    이 노드는:
    1. 검색 결과를 사용하여 섹션 내용을 작성합니다
    2. 섹션의 품질을 평가합니다
    3. 다음 중 하나를 수행합니다:
       - 품질이 충분하면 섹션을 완료합니다
       - 품질이 불충분하면 추가 연구를 트리거합니다
    
    Args:
        state: 검색 결과와 섹션 정보가 있는 현재 상태
        config: 작성 및 평가를 위한 구성
        
    Returns:
        섹션을 완료하거나 추가 연구를 수행하는 명령
    """

    # Get state 
    topic = state["topic"]
    section = state["section"]
    source_str = state["source_str"]

    # Get configuration
    configurable = Configuration.from_runnable_config(config)

    # Format system instructions
    section_writer_inputs_formatted = section_writer_inputs.format(topic=topic, 
                                                             section_name=section.name, 
                                                             section_topic=section.description, 
                                                             context=source_str, 
                                                             section_content=section.content)

    # Generate section  
    writer_provider = get_config_value(configurable.writer_provider)
    writer_model_name = get_config_value(configurable.writer_model)
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, temperature=0) 
    section_content = writer_model.invoke([SystemMessage(content=section_writer_instructions),
                                           HumanMessage(content=section_writer_inputs_formatted)])
    
    # Write content to the section object  
    section.content = section_content.content

    # Grade prompt 
    section_grader_message = """Grade the blog and consider follow-up questions for missing information.
                               If the grade is 'pass', return empty strings for all follow-up queries.
                               If the grade is 'fail', provide specific search queries to gather missing information."""
    
    section_grader_instructions_formatted = section_grader_instructions.format(topic=topic, 
                                                                               section_topic=section.description,
                                                                               section=section.content, 
                                                                               number_of_follow_up_queries=configurable.number_of_queries)

    # Use planner model for reflection
    planner_provider = get_config_value(configurable.planner_provider)
    planner_model = get_config_value(configurable.planner_model)
    if planner_model == "claude-3-7-sonnet-latest":
        # Allocate a thinking budget for claude-3-7-sonnet-latest as the planner model
        reflection_model = init_chat_model(model=planner_model, 
                                           model_provider=planner_provider, 
                                           max_tokens=20_000, 
                                           thinking={"type": "enabled", "budget_tokens": 16_000}).with_structured_output(Feedback)
    else:
        reflection_model = init_chat_model(model=planner_model, 
                                           model_provider=planner_provider).with_structured_output(Feedback)
    # Generate feedback
    feedback = reflection_model.invoke([SystemMessage(content=section_grader_instructions_formatted),
                                        HumanMessage(content=section_grader_message)])

    # If the section is passing or the max search depth is reached, publish the section to completed sections 
    if feedback.grade == "pass" or state["search_iterations"] >= configurable.max_search_depth:
        # Publish the section to completed sections 
        return Command(
        update={"completed_sections": [section]},
        goto=END
    )
    # Update the existing section with new content and update search queries
    else:
        return Command(
        update={"search_queries": feedback.follow_up_queries, "section": section},
        goto="search_web"
        )
    

def write_final_sections(state: SectionState, config: RunnableConfig):
    """연구가 필요하지 않은 섹션을 완료된 섹션을 컨텍스트로 사용하여 작성합니다.
    
    이 노드는 직접적인 연구보다는 연구된 섹션을 기반으로 하는 결론이나 요약과 같은 
    섹션을 처리합니다.
    
    Args:
        state: 완료된 섹션을 컨텍스트로 포함하는 현재 상태
        config: 작성 모델에 대한 구성
        
    Returns:
        새로 작성된 섹션을 포함하는 딕셔너리
    """

    # Get configuration
    configurable = Configuration.from_runnable_config(config)

    # Get state 
    topic = state["topic"]
    section = state["section"]
    completed_blog_sections = state["blog_sections_from_research"]
    
    # Format system instructions
    system_instructions = final_section_writer_instructions.format(topic=topic, section_name=section.name, section_topic=section.description, context=completed_blog_sections)

    # Generate section  
    writer_provider = get_config_value(configurable.writer_provider)
    writer_model_name = get_config_value(configurable.writer_model)
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, temperature=0) 
    section_content = writer_model.invoke([SystemMessage(content=system_instructions),
                                           HumanMessage(content="Generate a blog section based on the provided sources.")])
    
    # Write content to section 
    section.content = section_content.content

    # Write the updated section to completed sections
    return {"completed_sections": [section]} 