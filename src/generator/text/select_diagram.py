# src.generator.text.select_diagram.py
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


    def to_dict(self) -> Dict[str, Any]:
        """
        DiagramContent 객체를 dict로 변환하는 메서드
        """
        return {
            "title": self.title,
            "content": self.content,
            # "keywords": self.keywords or []
        }


class DiagramResult(BaseModel):
    """LLM이 최종 분류를 반환하는 모델"""
    diagram_name: str = Field(..., description="diagram 이름 card, image 중 하나를 선택해야합니다.")
    main_title: str = Field(..., description="핵심 주제(핵심키워드 조합)")
    sub_title_sections: List[DiagramContent] = Field(
        ..., 
        description="4개 이하의 sub title sections. 각 섹션은 반드시 'title'과 'content' 키를 포함해야 합니다."
    )
    keywords: List[str] = Field(..., description="a list of English keywords")

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
        """API 응답 형식으로 변환"""
        # 섹션 데이터 구성
        sections = []
        for i, section in enumerate(self.sub_title_sections):
            section_dict = section.to_dict()
            
            # 전체 키워드가 있고 섹션에 키워드가 없는 경우, 키워드를 할당
            if not section_dict.get("keywords") and self.keywords:
                # 섹션 제목과 관련된 키워드 필터링 (없으면 키워드 중 일부만 랜덤 할당)
                section_keywords = []
                for keyword in self.keywords:
                    # 키워드가 섹션 제목이나 내용에 포함되어 있으면 관련 키워드로 간주
                    if (
                        keyword.lower() in section_dict["title"].lower() or 
                        keyword.lower() in section_dict["content"].lower()
                    ):
                        section_keywords.append(keyword)
                
                # 관련 키워드가 없거나 너무 적으면 랜덤하게 일부 키워드 추가
                if len(section_keywords) < 2 and len(self.keywords) > 0:
                    import random
                    num_random = min(2, len(self.keywords))
                    random_keywords = random.sample(self.keywords, num_random)
                    
                    # 중복 제거
                    for kw in random_keywords:
                        if kw not in section_keywords:
                            section_keywords.append(kw)
                
                section_dict["keywords"] = section_keywords
            
            sections.append(section_dict)
        
        return {
            "diagram_name": self.diagram_name,
            "main_title": self.main_title,
            "sub_title_sections": sections,
            "keywords": self.keywords
        }


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """당신은 PPT 프리젠테이션에  제목과 서브 타이틀을 생성하는 전문가입니다.
 
"""
    ),
    (
        "human",
        """다음 텍스트를 분석하여 적절한 다이어그램을 선택하고, 제목과 서브 타이틀을 생성해 주세요:
        
{data}
        
텍스트 내용을 요약하여:
1. 텍스트의 핵심 주제를 명확히 표현하는 메인 타이틀을 생성하세요.
2. sections 갯수는 이야기의 주제 갯수만큼생성해야합니다 ex) 주제 1개면 1개, 주제 2개면 2개, 주제 3개면 3개, 주제 4개면 4개
3. 각 서브 타이틀은 반드시 'title'과 'content' 키를 포함해야 합니다.
4. title 30자 이내, content 는 100자 이내로 작성 
5. 키워드(keywords)는 영어로 작성해야합니다.
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

