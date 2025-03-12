from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from langgraph.constants import Send
from langgraph.graph import START, END, StateGraph
from langgraph.types import interrupt, Command

from src.state import (
    blogStateInput,
    blogStateOutput,
    Sections,
    blogState,
    SectionState,
    SectionOutputState,
    Queries,
    Feedback
)

from src.prompts import (
    blog_planner_query_writer_instructions,
    blog_planner_instructions,
    query_writer_instructions, 
    section_writer_instructions,
    final_section_writer_instructions,
    section_grader_instructions,
    section_writer_inputs
)

from src.configuration import Configuration
from src.utils import (
    format_sections, 
    get_config_value, 
    get_search_params, 
    select_and_execute_search
)

## Nodes -- 

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
    source_str = await select_and_execute_search(search_api, query_list, params_to_pass)

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

def human_feedback(state: blogState, config: RunnableConfig) -> Command[Literal["generate_blog_plan","build_section_with_web_research"]]:
    """보고서 계획에 대한 사용자 피드백을 받고 다음 단계로 라우팅합니다.
    
    이 노드는:
    1. 사용자 검토를 위해 현재 보고서 계획을 포맷합니다
    2. 인터럽트를 통해 피드백을 받습니다
    3. 다음 중 하나로 라우팅합니다:
       - 계획이 승인되면 섹션 작성으로 이동
       - 피드백이 제공되면 계획을 재생성
    
    Args:
        state: 검토할 섹션이 있는 현재 그래프 상태
        config: 워크플로우에 대한 구성
        
    Returns:
        계획을 재생성하거나 섹션 작성을 시작하는 명령
    """

    # Get sections
    topic = state["topic"]
    sections = state['sections']
    sections_str = "\n\n".join(
        f"Section: {section.name}\n"
        f"Description: {section.description}\n"
        f"Research needed: {'Yes' if section.research else 'No'}\n"
        for section in sections
    )

    # Get feedback on the blog plan from interrupt
    interrupt_message = f"""Please provide feedback on the following blog plan. 
                        \n\n{sections_str}\n
                        \nDoes the blog plan meet your needs?\nPass 'true' to approve the blog plan.\nOr, provide feedback to regenerate the blog plan:"""
    
    feedback = interrupt(interrupt_message)

    # If the user approves the blog plan, kick off section writing
    if isinstance(feedback, bool) and feedback is True:
        # Treat this as approve and kick off section writing
        return Command(goto=[
            Send("build_section_with_web_research", {"topic": topic, "section": s, "search_iterations": 0}) 
            for s in sections 
            if s.research
        ])
    
    # If the user provides feedback, regenerate the blog plan 
    elif isinstance(feedback, str):
        # Treat this as feedback
        return Command(goto="generate_blog_plan", 
                       update={"feedback_on_blog_plan": feedback})
    else:
        raise TypeError(f"Interrupt value of type {type(feedback)} is not supported.")
    
def generate_queries(state: SectionState, config: RunnableConfig):
    """특정 섹션을 연구하기 위한 검색 쿼리를 생성합니다.
    
    이 노드는 섹션 주제와 설명을 기반으로 타겟팅된 검색 쿼리를 생성하기 위해
    LLM을 사용합니다.
    
    Args:
        state: 섹션 세부 정보를 포함하는 현재 상태
        config: 생성할 쿼리 수를 포함한 구성
        
    Returns:
        생성된 검색 쿼리를 포함하는 딕셔너리
    """

    # Get state 
    topic = state["topic"]
    section = state["section"]

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    number_of_queries = configurable.number_of_queries

    # Generate queries 
    writer_provider = get_config_value(configurable.writer_provider)
    writer_model_name = get_config_value(configurable.writer_model)
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, temperature=0) 
    structured_llm = writer_model.with_structured_output(Queries)

    # Format system instructions
    system_instructions = query_writer_instructions.format(topic=topic, 
                                                           section_topic=section.description, 
                                                           number_of_queries=number_of_queries)

    # Generate queries  
    queries = structured_llm.invoke([SystemMessage(content=system_instructions),
                                     HumanMessage(content="Generate search queries on the provided topic.")])

    return {"search_queries": queries.queries}

async def search_web(state: SectionState, config: RunnableConfig):
    """섹션 쿼리에 대한 웹 검색을 실행합니다.
    
    이 노드는:
    1. 생성된 쿼리를 가져옵니다
    2. 구성된 검색 API를 사용하여 검색을 실행합니다
    3. 결과를 사용 가능한 컨텍스트로 포맷합니다
    
    Args:
        state: 검색 쿼리가 있는 현재 상태
        config: 검색 API 구성
        
    Returns:
        검색 결과와 업데이트된 반복 횟수가 포함된 딕셔너리
    """

    # Get state
    search_queries = state["search_queries"]

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    search_api = get_config_value(configurable.search_api)
    search_api_config = configurable.search_api_config or {}  # 구성 딕셔너리 가져오기, 기본값은 빈 딕셔너리
    params_to_pass = get_search_params(search_api, search_api_config)  # Filter parameters

    # Web search
    query_list = [query.search_query for query in search_queries]

    # Search the web with parameters
    source_str = await select_and_execute_search(search_api, query_list, params_to_pass)

    return {"source_str": source_str, "search_iterations": state["search_iterations"] + 1}

def write_section(state: SectionState, config: RunnableConfig) -> Command[Literal[END, "search_web"]]:
    """Write a section of the blog and evaluate if more research is needed.
    
    This node:
    1. Writes section content using search results
    2. Evaluates the quality of the section
    3. Either:
       - Completes the section if quality passes
       - Triggers more research if quality fails
    
    Args:
        state: Current state with search results and section info
        config: Configuration for writing and evaluation
        
    Returns:
        Command to either complete section or do more research
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
        return  Command(
        update={"completed_sections": [section]},
        goto=END
    )
    # Update the existing section with new content and update search queries
    else:
        return  Command(
        update={"search_queries": feedback.follow_up_queries, "section": section},
        goto="search_web"
        )
    
def write_final_sections(state: SectionState, config: RunnableConfig):
    """Write sections that don't require research using completed sections as context.
    
    This node handles sections like conclusions or summaries that build on
    the researched sections rather than requiring direct research.
    
    Args:
        state: Current state with completed sections as context
        config: Configuration for the writing model
        
    Returns:
        Dict containing the newly written section
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

def gather_completed_sections(state: blogState):
    """Format completed sections as context for writing final sections.
    
    This node takes all completed research sections and formats them into
    a single context string for writing summary sections.
    
    Args:
        state: Current state with completed sections
        
    Returns:
        Dict with formatted sections as context
    """
    # List of completed sections
    completed_sections = state["completed_sections"]

    # Format completed section to str to use as context for final sections
    completed_blog_sections = format_sections(completed_sections)

    return {"blog_sections_from_research": completed_blog_sections}

def compile_final_blog(state: blogState):
    """Compile all sections into the final blog.
    
    This node:
    1. Gets all completed sections
    2. Orders them according to original plan
    3. Combines them into the final blog
    
    Args:
        state: Current state with all completed sections
        
    Returns:
        Dict containing the complete blog
    """
    # Get sections
    sections = state["sections"]
    completed_sections = {s.name: s.content for s in state["completed_sections"]}

    # Update sections with completed content while maintaining original order
    for section in sections:
        section.content = completed_sections[section.name]

    # Compile final blog
    all_sections = "\n\n".join([s.content for s in sections])

    return {"final_blog": all_sections}

def initiate_final_section_writing(state: blogState):
    """Create parallel tasks for writing non-research sections.
    
    This edge function identifies sections that don't need research and
    creates parallel writing tasks for each one.
    
    Args:
        state: Current state with all sections and research context
        
    Returns:
        List of Send commands for parallel section writing
    """
    # Kick off section writing in parallel via Send() API for any sections that do not require research
    return [
        Send("write_final_sections", {"topic": state["topic"], "section": s, "blog_sections_from_research": state["blog_sections_from_research"]}) 
        for s in state["sections"] 
        if not s.research
    ]

# blog section sub-graph -- 

# Add nodes 
section_builder = StateGraph(SectionState, output=SectionOutputState)
section_builder.add_node("generate_queries", generate_queries)
section_builder.add_node("search_web", search_web)
section_builder.add_node("write_section", write_section)

# Add edges
section_builder.add_edge(START, "generate_queries")
section_builder.add_edge("generate_queries", "search_web")
section_builder.add_edge("search_web", "write_section")

# 최종 섹션 작성을 위한 초기 보고서 계획 컴파일하는 외부 그래프 -- 

# 노드 추가
builder = StateGraph(blogState, input=blogStateInput, output=blogStateOutput, config_schema=Configuration)
builder.add_node("generate_blog_plan", generate_blog_plan)
builder.add_node("human_feedback", human_feedback)
builder.add_node("build_section_with_web_research", section_builder.compile())
builder.add_node("gather_completed_sections", gather_completed_sections)
builder.add_node("write_final_sections", write_final_sections)
builder.add_node("compile_final_blog", compile_final_blog)

# 엣지 추가
builder.add_edge(START, "generate_blog_plan")
builder.add_edge("generate_blog_plan", "human_feedback")
builder.add_edge("build_section_with_web_research", "gather_completed_sections")
builder.add_conditional_edges("gather_completed_sections", initiate_final_section_writing, ["write_final_sections"])
builder.add_edge("write_final_sections", "compile_final_blog")
builder.add_edge("compile_final_blog", END)

graph = builder.compile()