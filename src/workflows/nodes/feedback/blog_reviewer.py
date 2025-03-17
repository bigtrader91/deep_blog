"""
블로그 계획 리뷰 및 피드백 노드

이 모듈은 블로그 계획에 대한 사용자 피드백을 수집하고 처리하는 노드를 제공합니다.
"""
from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.constants import Send
from langgraph.types import interrupt, Command

from src.workflows.states.blog_state import blogState, Section
from src.core.search.formatters import SectionFormatter


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
