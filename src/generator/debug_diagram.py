#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
다이어그램 생성기 디버깅 스크립트
"""
import sys
import os
from diagram_generator import generate_diagram_from_data

def main():
    """테스트용 간단한 예제를 실행합니다."""
    print("디버깅 스크립트 실행 시작...")
    
    # 간단한 테스트 데이터
    data = [
        {"title": "Test 1", "content": "Test content 1"},
        {"title": "Test 2", "content": "Test content 2"}
    ]
    
    # 출력 디렉토리 생성
    output_dir = "../output"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "debug_diagram.svg")
    
    print(f"데이터: {data}")
    print(f"출력 파일: {output_file}")
    
    # 함수 호출
    try:
        print("generate_diagram_from_data 함수 호출...")
        result = generate_diagram_from_data(data, output_file)
        print(f"결과: {result}")
        print("다이어그램 생성 성공!")
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc(file=sys.stdout)
    
    print("디버깅 스크립트 종료")

if __name__ == "__main__":
    main() 