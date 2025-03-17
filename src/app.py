"""
FastAPI 웹 서버

이 모듈은 블로그 생성 시스템의 REST API 엔드포인트를 제공합니다.
"""
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import uuid
import logging
from datetime import datetime

from src.workflows.workflow import generate_blog
from src.common.config.providers import set_config_value
from src.common.config import Configuration
from src.common.config.theme_styles import Theme

# 마크다운 변환 기능 추가
from src.workflows.graphs.markdown_workflow import convert_markdown_to_html

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="블로그 생성 API",
    description="AI 기반 블로그 콘텐츠 자동 생성 시스템",
    version="1.0.0",
)

# 현재 생성중인 블로그 작업 저장소
blog_jobs = {}


class BlogRequest(BaseModel):
    """블로그 생성 요청 모델
    
    Attributes:
        topic: 블로그 주제
        config: 선택적 구성 설정
    """
    topic: str = Field(..., description="블로그 포스트의 주제")
    config: Optional[Dict[str, Any]] = Field(None, description="워크플로우 구성 설정")


class BlogResponse(BaseModel):
    """블로그 생성 응답 모델
    
    Attributes:
        job_id: 작업 ID
        status: 작업 상태
        message: 상태 메시지
        blog: 생성된 블로그 콘텐츠 (완료된 경우)
    """
    job_id: str = Field(..., description="블로그 생성 작업의 고유 ID")
    status: str = Field(..., description="처리 상태 (pending, completed, failed)")
    message: str = Field(..., description="상태 메시지")
    blog: Optional[str] = Field(None, description="생성된 블로그 콘텐츠")


async def generate_blog_task(job_id: str, topic: str, config: Dict[str, Any] = None):
    """백그라운드 태스크로 블로그를 생성합니다.
    
    Args:
        job_id: 작업 ID
        topic: 블로그 주제
        config: 워크플로우 구성 설정
    """
    try:
        # 블로그 생성 작업 시작
        logger.info(f"블로그 생성 시작: 작업 ID {job_id}, 주제: '{topic}'")
        
        # 블로그 생성 실행
        blog_content = await generate_blog(topic, config)
        
        # 결과 저장
        blog_jobs[job_id]["status"] = "completed"
        blog_jobs[job_id]["blog"] = blog_content
        blog_jobs[job_id]["message"] = "블로그 생성이 완료되었습니다."
        blog_jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"블로그 생성 완료: 작업 ID {job_id}")
        
    except Exception as e:
        # 오류 처리
        error_msg = f"블로그 생성 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        blog_jobs[job_id]["status"] = "failed"
        blog_jobs[job_id]["message"] = error_msg
        blog_jobs[job_id]["completed_at"] = datetime.now().isoformat()


def markdown_to_html(markdown_text: str, theme_name: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """
    마크다운 텍스트를 HTML로 변환합니다.
    
    Args:
        markdown_text (str): 변환할 마크다운 텍스트
        theme_name (Optional[str], optional): 테마 이름 ('purple', 'green', 'blue', 'orange')
        output_path (Optional[str], optional): 결과를 저장할 파일 경로
        
    Returns:
        str: 변환된 HTML 코드
    """
    # 테마 설정
    theme = None
    if theme_name:
        try:
            theme = Theme(theme_name.lower())
        except ValueError:
            print(f"지원하지 않는 테마입니다: {theme_name}. 'purple', 'green', 'blue', 'orange' 중 하나를 사용하세요.")
            theme = Theme.PURPLE

    # 마크다운 변환 실행
    html_result = convert_markdown_to_html(markdown_text, theme)
    
    # 결과 저장
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_result)
        print(f"HTML이 저장되었습니다: {output_path}")
    
    return html_result


@app.post("/blog", response_model=BlogResponse, status_code=202)
async def create_blog(request: BlogRequest, background_tasks: BackgroundTasks):
    """블로그 생성 요청을 처리합니다.
    
    Args:
        request: 블로그 생성 요청 객체
        background_tasks: 백그라운드 작업 관리자
        
    Returns:
        작업 상태 정보가 포함된 응답
    """
    # 작업 ID 생성
    job_id = str(uuid.uuid4())
    
    # API 키 구성 처리
    config = request.config or {}
    
    # 작업 상태 초기화
    blog_jobs[job_id] = {
        "status": "pending",
        "message": "블로그 생성 작업이 큐에 추가되었습니다.",
        "created_at": datetime.now().isoformat(),
        "topic": request.topic,
    }
    
    # 백그라운드 작업 추가
    background_tasks.add_task(
        generate_blog_task,
        job_id=job_id,
        topic=request.topic,
        config=config
    )
    
    # 응답 반환
    return JSONResponse(
        content={
            "job_id": job_id,
            "status": "pending",
            "message": "블로그 생성 작업이 큐에 추가되었습니다."
        },
        status_code=202
    )


@app.get("/blog/{job_id}", response_model=BlogResponse)
async def get_blog_status(job_id: str):
    """블로그 생성 작업의 상태를 조회합니다.
    
    Args:
        job_id: 작업 ID
        
    Returns:
        작업 상태 정보가 포함된 응답
        
    Raises:
        HTTPException: 작업 ID가 존재하지 않는 경우
    """
    # 작업 ID 확인
    if job_id not in blog_jobs:
        raise HTTPException(status_code=404, detail=f"작업 ID '{job_id}'를 찾을 수 없습니다.")
    
    # 작업 상태 가져오기
    job = blog_jobs[job_id]
    
    # 응답 구성
    response = {
        "job_id": job_id,
        "status": job["status"],
        "message": job["message"],
    }
    
    # 완료된 경우 블로그 콘텐츠 추가
    if job["status"] == "completed" and "blog" in job:
        response["blog"] = job["blog"]
    
    return response


@app.get("/health")
async def health_check():
    """서버 상태 확인 엔드포인트입니다.
    
    Returns:
        서버 상태 정보
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    # 환경 변수에서 포트 가져오기 또는 기본값 8000 사용
    port = int(os.environ.get("PORT", 8000))
    
    # Uvicorn으로 서버 실행
    uvicorn.run("src.app:app", host="0.0.0.0", port=port, reload=True) 