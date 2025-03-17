"""
블로그 계획 노드 

이 모듈은 블로그 주제를 기반으로 섹션 구조를 계획하는 노드를 제공합니다.
"""
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.workflows.states.blog_state import blogState, Sections, Queries
from src.prompts import blog_planner_query_writer_instructions, blog_planner_instructions
from src.configuration import Configuration
from src.core.search.manager import SearchOrchestrator
from src.common.config.providers import get_config_value, get_search_params


async def generate_blog_plan(state: blogState, config: RunnableConfig):
    """초기 보고서 계획을 섹션과 함께 생성합니다.
    
    이 노드는:
    1. 보고서 구조 및 검색 매개변수에 대한 구성을 가져옵니다
    2. 계획을 위한 컨텍스트를 수집하기 위한 검색 쿼리를 생성합니다
    3. 해당 쿼리를 사용하여 웹 검색을 수행합니다
    4. LLM을 사용하여 섹션이 있는 구조화된 계획을 생성합니다
    
    Args:
        state: 보고서 주제를 포함하는 현재 그래프 상태
        config: 모델, 검색 API 등에 대한 구성
        
    Returns:
        생성된 섹션을 포함하는 딕셔너리
    """

    # Inputs
    topic = state["topic"]
    feedback = state.get("feedback_on_blog_plan", None)

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    blog_structure = configurable.blog_structure
    number_of_queries = configurable.number_of_queries
    search_api = get_config_value(configurable.search_api)
    search_api_config = configurable.search_api_config or {}  # 구성 딕셔너리 가져오기, 기본값은 빈 딕셔너리
    params_to_pass = get_search_params(search_api, search_api_config)  # 매개변수 필터링

    # Convert JSON object to string if necessary
    if isinstance(blog_structure, dict):
        blog_structure = str(blog_structure)

    # Set writer model (model used for query writing)
    writer_provider = get_config_value(configurable.writer_provider)
    writer_model_name = get_config_value(configurable.writer_model)
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, temperature=0) 
    structured_llm = writer_model.with_structured_output(Queries)

    # Format system instructions
    system_instructions_query = blog_planner_query_writer_instructions.format(topic=topic, blog_organization=blog_structure, number_of_queries=number_of_queries)

    # Generate queries  
    results = structured_llm.invoke([SystemMessage(content=system_instructions_query),
                                     HumanMessage(content="Generate search queries that will help with planning the sections of the blog.")])

    # Web search
    query_list = [query.search_query for query in results.queries]

    # Search the web with parameters
    orchestrator = SearchOrchestrator()
    source_str = await orchestrator.select_and_execute_search(search_api, query_list, params_to_pass)

    # Format system instructions
    system_instructions_sections = blog_planner_instructions.format(topic=topic, blog_organization=blog_structure, context=source_str, feedback=feedback)

    # Set the planner
    planner_provider = get_config_value(configurable.planner_provider)
    planner_model = get_config_value(configurable.planner_model)

    # blog planner instructions
    planner_message = """Generate the sections of the blog. Your response must include a 'sections' field containing a list of sections. 
                        Each section must have: name, description, plan, research, and content fields."""

    # Run the planner
    if planner_model == "claude-3-7-sonnet-latest":

        # Allocate a thinking budget for claude-3-7-sonnet-latest as the planner model
        planner_llm = init_chat_model(model=planner_model, 
                                      model_provider=planner_provider, 
                                      max_tokens=20_000, 
                                      thinking={"type": "enabled", "budget_tokens": 16_000})

    else:

        # With other models, we can use with_structured_output
        planner_llm = init_chat_model(model=planner_model, model_provider=planner_provider)
    
    # Generate the blog sections
    structured_llm = planner_llm.with_structured_output(Sections)
    blog_sections = structured_llm.invoke([SystemMessage(content=system_instructions_sections),
                                             HumanMessage(content=planner_message)])

    # Get sections
    sections = blog_sections.sections

    return {"sections": sections}
