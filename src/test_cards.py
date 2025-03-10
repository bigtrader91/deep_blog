#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
카드 다이어그램 생성기 테스트 스크립트
"""
from typing import List, Dict
import os
import sys
import importlib
import traceback

# 모듈 리로드를 위한 코드
if "card_generator" in sys.modules:
    print("card_generator 모듈이 이미 로드되어 있습니다. 리로드합니다.")
    importlib.reload(sys.modules["card_generator"])
else:
    print("card_generator 모듈을 새로 로드합니다.")

# 카드 생성기 가져오기
from card_generator import generate_card_from_data
from dotenv import load_dotenv

def test_card_generator():
    """
    카드 다이어그램 생성기 테스트
    """
    # 환경 변수 로드
    load_dotenv()
    
    # 출력 디렉토리 설정
    output_dir = "../output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 테스트 데이터
    test_data = [
        {
            "title": "건강 팁: 골밀도 향상을 위한 방법",
            "content": "매일 30분 이상 걷기, 칼슘이 풍부한 식품 섭취, 비타민 D 보충제 복용하기, 체중 부하 운동하기 등이 도움이 됩니다."
        },
        {
            "title": "골밀도 검사의 중요성",
            "content": "50세 이상은 정기적인 골밀도 검사를 통해 골다공증을 조기에 발견하는 것이 좋습니다. DEXA 스캔이 가장, 정확한 검사법입니다."
        }
    ]
    
    # 카드 다이어그램 생성 (pixabay_query 매개변수 없이)
    output_file1 = os.path.join(output_dir, "basic_card_test.svg")
    try:
        print("1. 기본 파라미터 테스트 (pixabay_query 없이)...")
        result1 = generate_card_from_data(
            test_data,
            output_file1,
            title="골밀도 관리의 중요성",
            background_color="#112233"
        )
        print(f"성공! 파일 생성됨: {result1}")
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        traceback.print_exc()
    
    # pixabay_query 매개변수를 포함한 테스트
    output_file2 = os.path.join(output_dir, "pixabay_card_test.svg")
    try:
        print("\n2. pixabay_query 파라미터 테스트...")
        
        # 함수 정의에 pixabay_query 매개변수가 있는지 출력
        import inspect
        params = inspect.signature(generate_card_from_data).parameters
        print("generate_card_from_data 함수의 매개변수:")
        for param in params.keys():
            print(f"  - {param}")
        
        if 'pixabay_query' in params:
            print("pixabay_query 매개변수가 존재합니다.")
            result2 = generate_card_from_data(
                test_data,
                output_file2,
                title="골밀도 관리의 중요성",
                background_color="#112233",
                pixabay_query="bone health exercise",
                pixabay_api_key=os.getenv("PIXABAY_API_KEY", "")
            )
            print(f"성공! 파일 생성됨: {result2}")
        else:
            print("pixabay_query 매개변수가 함수 정의에 없습니다!")
            print("함수를 다시 정의하거나 코드를 업데이트해야 합니다.")
    except TypeError as e:
        print(f"TypeError 발생: {str(e)}")
        print("generate_card_from_data 함수에 pixabay_query 매개변수가 정의되어 있지 않습니다.")
        print("card_generator.py 파일을 확인하고 필요한 경우 업데이트하세요.")
        traceback.print_exc()
    except Exception as e:
        print(f"기타 오류 발생: {str(e)}")
        traceback.print_exc()
    
    print("\n테스트 완료!")

if __name__ == "__main__":
    test_card_generator() 