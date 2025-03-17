"""
네이버 API 관련 유틸리티

이 모듈은 네이버 검색 API 및 네이버 검색광고 API와 상호작용하기 위한 다양한 유틸리티 함수를 제공합니다.
"""
import os
import re
import json
import time
import random
import requests
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import hashlib
import hmac
import base64
from urllib.parse import quote

from src.common.logging import get_logger

# 로거 설정
logger = get_logger(__name__)

def get_naver_api_keys() -> Tuple[str, str]:
    """
    환경 변수에서 네이버 API 키를 가져옵니다.
    
    Returns:
        Tuple[str, str]: (client_id, client_secret)
    """
    client_id = os.getenv("NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
    
    if not client_id or not client_secret:
        logger.warning("네이버 API 키가 설정되지 않았습니다. 환경 변수를 확인하세요.")
    
    return client_id, client_secret

def get_naver_searchad_keys() -> Tuple[str, str, str]:
    """
    환경 변수에서 네이버 검색광고 API 키를 가져옵니다.
    
    Returns:
        Tuple[str, str, str]: (api_key, secret_key, customer_id)
    """
    api_key = os.getenv("NAVER_API_KEY", "")
    secret_key = os.getenv("NAVER_SECRET_KEY", "")
    customer_id = os.getenv("NAVER_CUSTOMER_ID", "")
    
    if not api_key or not secret_key or not customer_id:
        logger.warning("네이버 검색광고 API 키가 설정되지 않았습니다. 환경 변수를 확인하세요.")
    
    return api_key, secret_key, customer_id

def get_naver_api_header() -> Dict[str, str]:
    """
    네이버 API 헤더를 생성합니다.
    
    Returns:
        Dict[str, str]: 네이버 API 요청 헤더
    """
    client_id, client_secret = get_naver_api_keys()
    return {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }

def get_naver_searchad_header(
    method: str = "GET", 
    path: str = "/keywordstool", 
    query: Dict[str, str] = {}
) -> Dict[str, str]:
    """
    네이버 검색광고 API 헤더를 생성합니다.
    
    Args:
        method: HTTP 메서드 (GET, POST 등)
        path: API 경로
        query: 쿼리 파라미터
        
    Returns:
        Dict[str, str]: 네이버 검색광고 API 요청 헤더
    """
    api_key, secret_key, customer_id = get_naver_searchad_keys()
    
    timestamp = str(int(time.time() * 1000))
    
    # 쿼리 파라미터 정렬 및 인코딩
    query_params = ""
    if query:
        query_params_list = []
        for key, value in sorted(query.items()):
            query_params_list.append(f"{key}={quote(str(value))}")
        query_params = "&".join(query_params_list)
    
    # 서명 생성
    message = f"{timestamp}.{method}.{path}"
    if query_params:
        message += f"?{query_params}"
    
    signature = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(signature).decode("utf-8")
    
    return {
        "Content-Type": "application/json",
        "X-Timestamp": timestamp,
        "X-API-KEY": api_key,
        "X-Customer": customer_id,
        "X-Signature": signature
    }


def get_relkeyword(keyword: str, search_count: int = 10) -> Dict[str, Any]:
    """
    네이버 검색광고 키워드 도구 API를 사용하여 연관 키워드를 조회합니다.
    
    Args:
        keyword: 검색할 키워드
        search_count: 조회할 키워드 수 (최대 100)
        
    Returns:
        Dict[str, Any]: 연관 키워드 정보
    """
    try:
        # API 엔드포인트 설정
        url = "https://api.naver.com/keywordstool"
        
        # 요청 파라미터 설정
        params = {
            "hintKeywords": keyword,
            "showDetail": 1
        }
        
        # API 요청 헤더 설정
        headers = get_naver_searchad_header(
            method="GET",
            path="/keywordstool",
            query=params
        )
        
        # API 요청 실행
        response = requests.get(url, headers=headers, params=params)
        
        # 응답 코드 확인
        if response.status_code != 200:
            logger.error(f"네이버 키워드 도구 API 오류: {response.status_code} - {response.text}")
            return {"error": f"API 오류: {response.status_code}", "message": response.text}
        
        # 응답 데이터 파싱
        result = response.json()
        
        return result
    
    except requests.RequestException as e:
        logger.error(f"네이버 키워드 도구 API 요청 중 오류 발생: {str(e)}")
        return {"error": "API 요청 실패", "message": str(e)}
    
    except Exception as e:
        logger.error(f"네이버 키워드 도구 조회 중 예외 발생: {str(e)}")
        return {"error": "예외 발생", "message": str(e)}

def get_keyword_trend(keyword: str, time_unit: str = "month", device: str = "all", ages: List[str] = ["1", "2"]) -> Dict[str, Any]:
    """
    네이버 검색광고 키워드 도구 API를 사용하여 키워드 트렌드를 조회합니다.
    
    Args:
        keyword: 검색할 키워드
        time_unit: 시간 단위 (month, week, date)
        device: 디바이스 (all, pc, mo)
        ages: 연령대 (1: 0-12세, 2: 13-19세, 3: 20-24세, 4: 25-29세, 5: 30-34세, 6: 35-39세, 7: 40-44세, 8: 45-49세, 9: 50-54세, 10: 55-60세, 11: 60세 이상)
        
    Returns:
        Dict[str, Any]: 키워드 트렌드 정보
    """
    try:
        # API 엔드포인트 설정
        url = "https://api.naver.com/keywordstool"
        
        # 요청 파라미터 설정
        params = {
            "hintKeywords": keyword,
            "showDetail": 1,
            "timeUnit": time_unit,
            "device": device,
            "ages": ",".join(ages)
        }
        
        # API 요청 헤더 설정
        headers = get_naver_searchad_header(
            method="GET",
            path="/keywordstool",
            query=params
        )
        
        # API 요청 실행
        response = requests.get(url, headers=headers, params=params)
        
        # 응답 코드 확인
        if response.status_code != 200:
            logger.error(f"네이버 키워드 도구 API 오류: {response.status_code} - {response.text}")
            return {"error": f"API 오류: {response.status_code}", "message": response.text}
        
        # 응답 데이터 파싱
        result = response.json()
        
        return result
    
    except requests.RequestException as e:
        logger.error(f"네이버 키워드 도구 API 요청 중 오류 발생: {str(e)}")
        return {"error": "API 요청 실패", "message": str(e)}
    
    except Exception as e:
        logger.error(f"네이버 키워드 트렌드 조회 중 예외 발생: {str(e)}")
        return {"error": "예외 발생", "message": str(e)}

def collect_related_keywords(keyword: str, save_results: bool = False) -> Dict[str, Any]:
    """
    키워드의 연관 키워드를 수집하고 포맷팅합니다.
    
    Args:
        keyword: 검색할 키워드
        save_results: 검색 결과를 파일로 저장할지 여부
        
    Returns:
        Dict[str, Any]: 연관 키워드 정보
    """
    try:
        # 키워드 전처리
        keyword = keyword.strip()
        if not keyword:
            return {"error": "키워드가 비어있습니다."}
        
        # API 요청
        result = get_relkeyword(keyword)
        
        if "error" in result:
            return result
        
        # 검색 결과 포맷팅
        formatted_result = {
            "keyword": keyword,
            "relKeywords": []
        }
        
        if "keywordList" in result:
            formatted_result["relKeywords"] = result["keywordList"]
            
            # 검색량 및 경쟁률 정보 추가
            for item in formatted_result["relKeywords"]:
                # PC 및 모바일 검색량 합산
                if "monthlyPcQcCnt" in item and "monthlyMobileQcCnt" in item:
                    pc_count = item["monthlyPcQcCnt"] if item["monthlyPcQcCnt"] != "< 10" else 10
                    mobile_count = item["monthlyMobileQcCnt"] if item["monthlyMobileQcCnt"] != "< 10" else 10
                    
                    try:
                        total_count = int(pc_count) + int(mobile_count)
                        item["totalSearchCount"] = total_count
                    except ValueError:
                        item["totalSearchCount"] = 0
                
                # 경쟁정도 카테고리화
                if "compIdx" in item:
                    comp_idx = item["compIdx"]
                    if comp_idx >= 0.8:
                        item["competition"] = "높음"
                    elif comp_idx >= 0.4:
                        item["competition"] = "중간"
                    else:
                        item["competition"] = "낮음"
        
        # 검색 결과 파일로 저장
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"related_keywords_{keyword}_{timestamp}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(formatted_result, f, ensure_ascii=False, indent=2)
            logger.info(f"연관 키워드 저장 완료: {filename}")
        
        return formatted_result
    
    except Exception as e:
        logger.error(f"연관 키워드 수집 중 예외 발생: {str(e)}")
        return {"error": "예외 발생", "message": str(e)} 