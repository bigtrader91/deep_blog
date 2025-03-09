from typing import Annotated, List, TypedDict, Literal
from pydantic import BaseModel, Field
import operator

class Section(BaseModel):
    name: str = Field(
        description="보고서의 이 섹션에 대한 이름.",
    )
    description: str = Field(
        description="이 섹션에서 다룰 주요 주제와 개념에 대한 간략한 개요.",
    )
    research: bool = Field(
        description="보고서의 이 섹션에 대해 웹 연구를 수행할지 여부."
    )
    content: str = Field(
        description="섹션의 내용."
    )   

class Sections(BaseModel):
    sections: List[Section] = Field(
        description="보고서의 섹션들.",
    )

class SearchQuery(BaseModel):
    search_query: str = Field(None, description="웹 검색을 위한 쿼리.")

class Queries(BaseModel):
    queries: List[SearchQuery] = Field(
        description="검색 쿼리 목록.",
    )

class Feedback(BaseModel):
    grade: Literal["pass","fail"] = Field(
        description="응답이 요구 사항을 충족하는지('pass') 또는 수정이 필요한지('fail')를 나타내는 평가 결과."
    )
    follow_up_queries: List[SearchQuery] = Field(
        description="후속 검색 쿼리 목록.",
    )

class ReportStateInput(TypedDict):
    topic: str # 보고서 주제
    
class ReportStateOutput(TypedDict):
    final_report: str # 최종 보고서

class ReportState(TypedDict):
    topic: str # 보고서 주제    
    feedback_on_report_plan: str # 보고서 계획에 대한 피드백
    sections: list[Section] # 보고서 섹션 목록 
    completed_sections: Annotated[list, operator.add] # Send() API 키
    report_sections_from_research: str # 최종 섹션을 작성하기 위한 연구 결과로부터의 완성된 섹션 문자열
    final_report: str # 최종 보고서

class SectionState(TypedDict):
    topic: str # 보고서 주제
    section: Section # 보고서 섹션  
    search_iterations: int # 수행된 검색 반복 횟수
    search_queries: list[SearchQuery] # 검색 쿼리 목록
    source_str: str # 웹 검색에서 형식화된 소스 내용 문자열
    report_sections_from_research: str # 최종 섹션을 작성하기 위한 연구 결과로부터의 완성된 섹션 문자열
    completed_sections: list[Section] # Send() API를 위해 외부 상태에 복제하는 최종 키

class SectionOutputState(TypedDict):
    completed_sections: list[Section] # Send() API를 위해 외부 상태에 복제하는 최종 키