import os
import urllib.request
import urllib.parse
import json
from typing import Dict, List, TypedDict, Any, Optional
from dotenv import load_dotenv

# ----- langchain + openai_functions 관련 임포트
from langchain.chains.openai_functions import create_structured_output_runnable
# (환경에 맞게 langchain 관련 패키지를 교체하세요)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

load_dotenv()  # .env에서 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 로드

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

class LLMTitleResult(BaseModel):
    """LLM이 최종 분류를 반환"""
    title: str = Field(..., description="블로그 제목")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "당신은 네이버 쇼핑검색 결과에 대한 전문 분석가입니다. "
        "{data}에 대한 블로그 제목을 생성해 주세요."
    ),
    (
        "human",
        "블로그 제목을 생성해 주세요. "
        "블로그 제목에는 리뷰, 사용방법 등 제품사진이 필요한 제목은 제외해야합니다다"
    ),
])

llm_chain = prompt | llm.with_structured_output(LLMTitleResult)

def generate_title(data: str) -> str:
    """
    data: 네이버 쇼핑검색 결과
    return: 블로그 제목
    """
    try:
        return llm_chain.invoke({"data": data}).title
    except Exception as e:
        print(f"Error generating title: {e}")
        return ""
