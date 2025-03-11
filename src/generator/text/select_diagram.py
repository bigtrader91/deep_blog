"""
다이어그램 선택 및 분석을 위한 모듈
"""
import os
import urllib.request
import urllib.parse
import json
import logging
from typing import Dict, List, TypedDict, Any, Optional
from dotenv import load_dotenv
from langchain.chains.openai_functions import create_structured_output_runnable
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# pydantic v2 직접 임포트로 변경
try:
    from pydantic import BaseModel, Field
except ImportError:
    # 호환성을 위한 대체 임포트
    from pydantic.v1 import BaseModel, Field

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DiagramContent(BaseModel):
    """다이어그램의 섹션 내용을 정의하는 모델"""
    title: str = Field(..., description="서브 타이틀(키워드)")
    content: str = Field(..., description="서브 타이틀에 대한 내용")

    def to_dict(self) -> Dict[str, str]:
        """딕셔너리 형태로 변환"""
        return {
            "title": self.title,
            "content": self.content
        }


class DiagramResult(BaseModel):
    """LLM이 최종 분류를 반환하는 모델"""
    diagram_name: str = Field(..., description="diagram 이름 card, image 중 하나를 선택해야합니다.")
    main_title: str = Field(..., description="핵심 주제(핵심키워드 조합)")
    sub_title_sections: List[DiagramContent] = Field(
        ..., 
        description="5개 이하의 sub title sections. 각 섹션은 반드시 'title'과 'content' 키를 포함해야 합니다."
    )

    @classmethod
    def with_fallback(cls, diagram_name: str, main_title: str, sections: Optional[List[Dict[str, str]]] = None):
        """
        유효하지 않은 경우 기본값으로 대체하여 인스턴스를 생성합니다.
        
        Args:
            diagram_name: 다이어그램 이름
            main_title: 메인 타이틀
            sections: 서브 타이틀 섹션들 (없으면 기본값 사용)
            
        Returns:
            DiagramResult: 유효한 DiagramResult 인스턴스
        """
        if not sections:
            sections = [
                {"title": "섹션 1", "content": "내용이 생성되지 않았습니다."},
                {"title": "섹션 2", "content": "내용이 생성되지 않았습니다."}
            ]
        
        # DiagramContent 객체 리스트 생성
        valid_sections = []
        for section in sections:
            content = DiagramContent(
                title=section.get("title", "제목 없음"),
                content=section.get("content") or section.get("description") or section.get("text") or "내용 없음"
            )
            valid_sections.append(content)
        
        # 섹션 수에 따라 다이어그램 유형 항상 자동 결정 (입력된 diagram_name 무시)
        diagram_name = "card" if len(valid_sections) > 2 else "image"
        logger.info(f"섹션 수({len(valid_sections)})에 따라 자동 결정된 다이어그램 유형: {diagram_name}")
        
        return cls(
            diagram_name=diagram_name,
            main_title=main_title,
            sub_title_sections=valid_sections
        )

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 변환"""
        return {
            "diagram_name": self.diagram_name,
            "main_title": self.main_title,
            "sub_title_sections": [section.to_dict() for section in self.sub_title_sections]
        }


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """당신은 PPT 프리젠테이션에 사용할 다이어그램을 선택하고 제목과 서브 타이틀을 생성하는 전문가입니다.
 
출력 형식이 매우 중요합니다. 반드시 다음 형식을 지켜주세요:
        
```json
{{
    "diagram_name": "card 또는 image 중 하나",
    "main_title": "핵심 주제",
    "sub_title_sections": [
        {{"title": "서브 타이틀 1", "content": "내용 1"}},
        {{"title": "서브 타이틀 2", "content": "내용 2"}}
    ]
}}
```

참고: 실제 diagram_name은 섹션 수에 따라 자동으로 결정됩니다:
- 섹션이 3개 이상이면 자동으로 'card' 다이어그램이 사용됩니다.
- 섹션이 2개 이하면 자동으로 'image' 다이어그램이 사용됩니다.

따라서 diagram_name 필드는 실제로는 무시되고 섹션 수에 따라 자동 결정됩니다.
        
sub_title_sections은 반드시 2개 이상, 5개 이하로 생성해야 하며, 각 항목은 반드시 'title'과 'content' 키를 포함해야 합니다.
다른 형식의 키(예: 'description', 'text' 등)는 사용하지 마세요.
"""
    ),
    (
        "human",
        """다음 텍스트를 분석하여 적절한 다이어그램을 선택하고, 제목과 서브 타이틀을 생성해 주세요:
        
{data}
        
텍스트 내용을 분석하여:
1. 텍스트의 특성, 구조, 내용에 따라 가장 적합한 다이어그램 유형(card, image)을 선택하세요.
2. 텍스트의 핵심 주제를 명확히 표현하는 메인 타이틀을 생성하세요.
3. 내용을 잘 구조화하여 2-5개의 서브 타이틀과 그에 맞는 내용을 생성하세요.
        
각 서브 타이틀 섹션은 반드시 'title'과 'content' 키를 포함해야 합니다.

"""
    ),
])

# function_calling 방법 명시적 지정으로 경고 해결
llm_chain = prompt | llm.with_structured_output(DiagramResult, method="function_calling")

def select_diagram(data: str) -> DiagramResult:
    """
    텍스트 데이터를 분석하여 적절한 다이어그램 유형, 제목, 서브 타이틀을 선택합니다.
    
    Args:
        data: 분석할 텍스트
        
    Returns:
        DiagramResult: 다이어그램 정보
    """
    try:
        logger.info("LLM에 텍스트 분석 요청 시작")
        logger.debug(f"입력 텍스트 길이: {len(data)} 글자")
        
        result = llm_chain.invoke({"data": data})
        
        # 섹션 수에 따라 다이어그램 유형 항상 자동 결정 (LLM이 선택한 것 무시)
        section_count = len(result.sub_title_sections)
        result.diagram_name = "card" if section_count > 2 else "image"
        
        logger.info(f"섹션 수({section_count})에 따라 자동 결정된 다이어그램 유형: {result.diagram_name}")
        logger.info(f"생성된 주제: {result.main_title}")
        logger.info(f"생성된 섹션 수: {len(result.sub_title_sections)}개")
        
        return result
    except Exception as e:
        logger.error(f"오류 발생: {str(e)}")
        # 오류 발생 시 기본값으로 대체
        main_title = "텍스트 분석 결과" if not data else data.split('\n')[0][:30] + "..."
        logger.warning(f"기본값으로 대체: {main_title}")
        return DiagramResult.with_fallback("card", main_title, None)


if __name__ == "__main__":
    # 테스트
    test_text = """
    봉준호 감독의 영화 '미키17'이 지난 7일 중국 주요 도시에서 개봉했다. 2016년 사드(THAAD·고고도미사일방어체계) 사태 이후 중국에 유통된 한국 영화는 '오! 문희', '강변호텔' 2건에 불과했다. 봉준호 감독의 신작 '미키17'은 할리우드 자본으로 제작됐지만, 한국 감독의 작품이라는 점에서 업계에서는 중국의 한한령 완화 움직임과 연결 짓는 해석이 나오고 있다.
    
    중국의 한한령 해제 조짐에 급등한 제작비로 위기를 겪고 있는 한국 콘텐츠 사업 붐이 다시 일어나리란 기대가 곳곳에서 흘러나오고 있다. 하지만 정작 현장에 있는 당사자들은 "그동안 중국 내 분위기는 급변했는데, 한국은 이에 대항할만한 준비가 정책적으로 전혀 돼 있지 않다"고 우려했다.
    """
    
    try:
        result = select_diagram(test_text)
        print("\n다이어그램 분석 결과:")
        print(f"다이어그램 유형: {result.diagram_name}")
        print(f"메인 타이틀: {result.main_title}")
        print(f"섹션 수: {len(result.sub_title_sections)}개")
        for i, section in enumerate(result.sub_title_sections):
            print(f"\n[섹션 {i+1}]")
            print(f"제목: {section.title}")
            print(f"내용: {section.content[:50]}...")
    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {str(e)}")

