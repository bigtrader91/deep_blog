#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
주피터 노트북에서 카드 생성기를 사용하는 예제 코드

이 파일은 주피터 노트북에 복사하여 실행할 수 있는 예제 코드입니다.
"""

# 필요한 모듈 설치
# !pip install svgwrite requests python-dotenv

# src 디렉토리를 sys.path에 추가
import os
import sys
import importlib

# 현재 노트북 실행 경로 확인
current_path = os.getcwd()
print(f"현재 실행 경로: {current_path}")

# src 디렉토리 경로 설정 (필요에 따라 수정)
src_path = os.path.join(current_path, "src")
if os.path.exists(src_path):
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        print(f"{src_path}를 sys.path에 추가했습니다.")
    else:
        print(f"{src_path}는 이미 sys.path에 있습니다.")
else:
    print(f"경고: {src_path} 디렉토리가 존재하지 않습니다. 경로를 확인하세요.")

# 모듈 리로드 (이미 로드된 경우)
if "card_generator" in sys.modules:
    print("card_generator 모듈을 리로드합니다.")
    importlib.reload(sys.modules["card_generator"])
else:
    print("card_generator 모듈을 처음 로드합니다.")

# 헬퍼 모듈 사용 또는 직접 함수 호출
try:
    # 1. 헬퍼 모듈 사용 (추천 방법)
    from src.notebook_helper import generate_card_safe, get_example_data
    
    # 출력 디렉토리 설정
    output_dir = os.path.join(current_path, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 예제 데이터 가져오기
    example_data = get_example_data()
    
    # 카드 다이어그램 생성 (안전한 방법)
    output_file = os.path.join(output_dir, "notebook_example.svg")
    result = generate_card_safe(
        data=example_data,
        output_file=output_file,
        title="골밀도 관리 가이드",
        background_color="#0F3B5F",
        header_color="#FFFFFF",
        pixabay_query="bone health exercise",  # 조건부로 전달됨
        pixabay_api_key=""  # 여기에 API 키 입력
    )
    
    print(f"카드 다이어그램 생성 완료: {result}")
    
    # SVG 파일 미리보기 (IPython이 설치된 경우)
    from IPython.display import SVG, display
    display(SVG(filename=output_file))
    
except ImportError:
    # 2. 직접 import하는 방법 (대체 방법)
    print("헬퍼 모듈을 찾을 수 없습니다. 직접 import 방법을 사용합니다.")
    
    # 카드 생성기 직접 import
    try:
        from card_generator import generate_card_from_data
        
        # 출력 디렉토리 설정
        output_dir = os.path.join(current_path, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # 예제 데이터
        example_data = [
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
        
        # 카드 다이어그램 생성 (직접 호출 방법)
        output_file = os.path.join(output_dir, "notebook_example_direct.svg")
        
        # pixabay 매개변수 관련 오류 처리
        import inspect
        fn_params = inspect.signature(generate_card_from_data).parameters
        has_pixabay_params = 'pixabay_query' in fn_params
        
        if has_pixabay_params:
            result = generate_card_from_data(
                data=example_data,
                output_file=output_file,
                title="골밀도 관리 가이드",
                background_color="#0F3B5F",
                header_color="#FFFFFF",
                pixabay_query="bone health exercise",
                pixabay_api_key=""  # 여기에 API 키 입력
            )
        else:
            # pixabay 매개변수가 없는 경우
            result = generate_card_from_data(
                data=example_data,
                output_file=output_file,
                title="골밀도 관리 가이드",
                background_color="#0F3B5F",
                header_color="#FFFFFF"
            )
        
        print(f"카드 다이어그램 생성 완료: {result}")
        
        # SVG 파일 미리보기 (IPython이 설치된 경우)
        try:
            from IPython.display import SVG, display
            display(SVG(filename=output_file))
        except ImportError:
            print("IPython이 설치되어 있지 않아 미리보기를 표시할 수 없습니다.")
    
    except ImportError:
        print("오류: card_generator 모듈을 import할 수 없습니다. 경로를 확인하세요.")
        
print("\n스크립트 실행 완료!") 