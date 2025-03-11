# src.generator.svg.common_utils.py
"""
SVG 다이어그램 생성에 사용되는 공통 유틸리티 모듈

이 모듈은 외부 API 호출, 이미지 처리, 키워드 생성 등
다이어그램 생성 과정에서 공통으로 사용되는 기능들을 제공합니다.
"""
import random
import logging
import requests
from typing import List, Optional, Dict, Union, Any
from urllib.parse import quote, urlparse
import os
import re
# 랜덤 이미지 검색에 사용할 키워드 목록
RANDOM_KEYWORDS = [
    "abstract", "nature", "texture", "pattern", "background", 
    "gradient", "landscape", "mountains", "ocean", "forest",
    "sky", "clouds", "sunset", "technology", "business",
    "minimalist", "geometric", "space", "stars", "universe",
    "water", "fire", "earth", "air", "light"
]

logger = logging.getLogger(__name__)

def get_random_keywords(base_keyword: str = "", count: int = 2) -> str:
    """
    랜덤한 검색 키워드를 생성합니다.

    Args:
        base_keyword: 기본 키워드 (빈 문자열이면 완전히 랜덤)
        count: 추가할 랜덤 키워드 수

    Returns:
        str: 랜덤하게 생성된 검색 키워드
    """
    if not base_keyword:
        base_keyword = random.choice(RANDOM_KEYWORDS)
    additional = random.sample(RANDOM_KEYWORDS, min(count, len(RANDOM_KEYWORDS)))
    return f"{base_keyword} {' '.join(additional)}"

def remove_korean(text: str) -> str:
    """
    입력 문자열에서 한글을 제거합니다.
    """
    # 한글 범위: \uac00-\ud7af
    return re.sub(r'[\uac00-\ud7af]+', '', text)

def clean_query(query: str) -> str:
    """
    검색 쿼리에서 한글과 쉼표 및 불필요한 공백을 제거합니다.
    """
    # 한글 제거
    query = remove_korean(query)
    # 쉼표 제거
    query = query.replace(',', '')
    # 여러 공백을 하나의 공백으로 정리
    query = ' '.join(query.split())
    query = query[0:30]
    return query

def get_pixabay_image(
    query: str,
    api_key: str,
    width: int = 800,
    height: int = 400,
    random_select: bool = True
) -> Optional[str]:
    """
    픽사베이 API를 사용하여 이미지를 검색하고 URL을 반환합니다.
    쿼리 문자열에서 한글과 쉼표 등 불필요한 문자를 제거합니다.
    
    Args:
        query: 검색어
        api_key: 픽사베이 API 키
        width: 요청할 이미지 너비
        height: 요청할 이미지 높이
        random_select: 검색 결과에서 랜덤하게 선택할지 여부
        
    Returns:
        Optional[str]: 이미지 URL 또는 실패 시 None
    """
    try:
        # 쿼리 정리: 한글, 쉼표 제거 및 공백 정리
        query = clean_query(query)
        logger.info(f"한글 제거 후 검색어: {query}")
        
        encoded_query = quote(query)
        url = (
            f"https://pixabay.com/api/?key={api_key}&q={encoded_query}"
            f"&image_type=photo&orientation=horizontal&per_page=20"
            f"&min_width={width}&min_height={height}&safesearch=true"
        )
        
        logger.debug(f"픽사베이 API 요청 URL: {url}")
        response = requests.get(url)
        data = response.json()
        
        if data.get('totalHits', 0) > 0:
            if random_select and len(data['hits']) > 1:
                random_index = random.randint(0, len(data['hits']) - 1)
                selected_url = data['hits'][random_index]['largeImageURL']
                logger.debug(f"픽사베이 이미지 선택 (랜덤): {selected_url}")
                return selected_url
            else:
                selected_url = data['hits'][0]['largeImageURL']
                logger.debug(f"픽사베이 이미지 선택 (첫번째): {selected_url}")
                return selected_url
        else:
            logger.warning(f"'{query}' 검색 결과 없음 - 대체 키워드로 재시도합니다.")
            query_without_bg = query.lower().replace('background', '').strip()
            if query_without_bg and query_without_bg != query.lower():
                return get_pixabay_image(query_without_bg, api_key, width, height, random_select)
            
            fallback_keywords = [
                "modern abstract", "digital background", "minimalist texture",
                "geometric pattern", "gradient background", "business background"
            ]
            for keyword in fallback_keywords:
                if query.lower() != keyword.lower():
                    return get_pixabay_image(keyword, api_key, width, height, random_select)
            
            logger.error("모든 대체 키워드로 검색 실패")
            return None
    except Exception as e:
        logger.error(f"픽사베이 API 오류: {str(e)}")
        return None

def get_keywords_from_sections(sections: List[Dict[str, Any]], max_keywords: int = 5) -> str:
    """
    섹션 데이터에서 키워드를 추출하여 검색 쿼리를 생성합니다.
    
    Args:
        sections: 섹션 데이터 리스트
        max_keywords: 최대 키워드 수
        
    Returns:
        str: 검색 쿼리
    """
    all_keywords = []
    
    # 먼저 명시적 키워드 수집
    for section in sections:
        if 'keywords' in section and isinstance(section['keywords'], list):
            all_keywords.extend(section['keywords'])
    
    # 명시적 키워드가 충분하지 않으면 제목과 내용에서 키워드 추출
    if len(all_keywords) < max_keywords:
        for section in sections:
            if 'title' in section:
                # 제목에서 키워드 추출 (2단어 이상만 포함)
                words = section['title'].split()
                for word in words:
                    if len(word) >= 2 and word.lower() not in [k.lower() for k in all_keywords]:
                        all_keywords.append(word)
            
            # 내용에서도 키워드 추출
            if 'content' in section and len(all_keywords) < max_keywords:
                words = section['content'].split()
                for word in words:
                    if len(word) >= 3 and word.lower() not in [k.lower() for k in all_keywords]:
                        all_keywords.append(word)
    
    # 중복 제거 및 최대 키워드 수 제한
    unique_keywords = []
    for kw in all_keywords:
        if kw.lower() not in [k.lower() for k in unique_keywords]:
            unique_keywords.append(kw)
    
    # 최대 키워드 수만큼 선택
    selected_keywords = unique_keywords[:max_keywords]
    
    # 키워드가 없으면 섹션 제목을 기반으로 한 기본 키워드 사용
    if not selected_keywords:
        if sections and 'title' in sections[0]:
            return f"{sections[0]['title']} background"
        return "abstract modern background"
    
    # 키워드에 'background' 추가
    if 'background' not in ' '.join(selected_keywords).lower():
        selected_keywords.append('background')
    
    return ' '.join(selected_keywords)

def validate_image_url(url: str) -> bool:
    """
    이미지 URL이 유효한지 확인합니다.
    
    Args:
        url: 확인할 URL
        
    Returns:
        bool: 유효한 URL이면 True, 아니면 False
    """
    # URL 구문 확인
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False
            
        # 이미지 확장자 확인
        image_extensions = ['.jpg', '.jpeg', '.png', '.svg', '.gif', '.webp']
        path_lower = result.path.lower()
        if not any(path_lower.endswith(ext) for ext in image_extensions):
            # 확장자가 없으면 URL에 이미지 파라미터가 있는지 확인
            if 'image' not in url.lower() and 'img' not in url.lower():
                return False
        
        return True
    except:
        return False 