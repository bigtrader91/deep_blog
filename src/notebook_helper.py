#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
주피터 노트북에서 card_generator 사용을 도와주는 헬퍼 모듈

이 모듈은 주피터 노트북에서 card_generator 모듈을 사용할 때 발생할 수 있는
경로 문제와 모듈 캐싱 문제를 해결합니다.
"""
import os
import sys
import importlib
import inspect
from typing import List, Dict, Optional

def setup_path():
    """
    src 디렉토리를 sys.path에 추가하여 모듈을 올바르게 import할 수 있게 합니다.
    """
    # 현재 스크립트의 위치
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # src 디렉토리가 이미 sys.path에 있는지 확인
    if current_dir not in sys.path:
        print(f"{current_dir}를 sys.path에 추가합니다.")
        sys.path.insert(0, current_dir)
    else:
        print(f"{current_dir}는 이미 sys.path에 있습니다.")
    
    # 모듈 캐시 삭제
    modules_to_reload = ["card_generator"]
    for module in modules_to_reload:
        if module in sys.modules:
            print(f"{module} 모듈을 리로드합니다.")
            importlib.reload(sys.modules[module])
        else:
            print(f"{module} 모듈은 아직 로드되지 않았습니다.")

def generate_card_safe(
    data: List[Dict[str, str]], 
    output_file: str, 
    title: str = "골밀도란 무엇인가?",
    card_color: str = "#FEEBDC",
    title_color: str = "#333333",
    content_color: str = "#333333",
    size: int = 800,  # 정사각형 사이즈 (1:1 비율)
    background_color: str = "#111111",
    background_image: Optional[str] = None,
    header_image: Optional[str] = None,
    header_image_height: int = 300,
    header_color: str = "#FFFFFF",
    rounded_corners: int = 10,
    card_padding: int = 30,
    vertical_spacing: int = 20,
    add_responsive: bool = True,
    pixabay_query: Optional[str] = None,
    pixabay_api_key: Optional[str] = None
) -> str:
    """
    card_generator의 generate_card_from_data 함수를 안전하게 호출합니다.
    
    주피터 노트북에서 발생할 수 있는 키워드 인자 문제를 방지하기 위해
    pixabay 관련 매개변수를 조건부로 전달합니다.
    
    Returns:
        str: 생성된 SVG 파일 경로
    """
    # 모듈 임포트 (경로 설정 후)
    setup_path()
    from card_generator import generate_card_from_data
    
    # 매개변수 구성
    params = {
        'data': data,
        'output_file': output_file,
        'title': title,
        'card_color': card_color,
        'title_color': title_color,
        'content_color': content_color,
        'size': size,
        'background_color': background_color,
        'background_image': background_image,
        'header_image': header_image,
        'header_image_height': header_image_height,
        'header_color': header_color,
        'rounded_corners': rounded_corners,
        'card_padding': card_padding,
        'vertical_spacing': vertical_spacing,
        'add_responsive': add_responsive
    }
    
    # generate_card_from_data 함수의 매개변수 목록 확인
    fn_params = inspect.signature(generate_card_from_data).parameters
    
    # pixabay 관련 매개변수가 함수에 정의되어 있는 경우에만 추가
    if 'pixabay_query' in fn_params and pixabay_query is not None:
        params['pixabay_query'] = pixabay_query
    
    if 'pixabay_api_key' in fn_params and pixabay_api_key is not None:
        params['pixabay_api_key'] = pixabay_api_key
    
    # 함수 호출
    return generate_card_from_data(**params)

def get_example_data() -> List[Dict[str, str]]:
    """
    예제 데이터를 반환합니다.
    """
    return [
        {
            "title": "골밀도란 무엇인가?",
            "content": "골밀도는 뼈의 강도와 건강을 나타내는 지표입니다. 낮은 골밀도는 골다공증과 골절 위험을 증가시킵니다."
        },
        {
            "title": "골밀도 검사",
            "content": "DEXA 스캔은 가장 정확한 골밀도 측정 방법입니다. 일반적으로 65세 이상 여성과 70세 이상 남성에게 권장됩니다."
        },
        {
            "title": "골밀도 향상 방법",
            "content": "칼슘과 비타민 D가 풍부한 식품 섭취, 규칙적인 체중 부하 운동, 금연, 적절한 체중 유지가 도움이 됩니다."
        }
    ] 