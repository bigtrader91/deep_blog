#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
40:60 비율의 이미지-텍스트 레이아웃 테스트 스크립트입니다.

이 스크립트는 split_layout_generator 모듈을 사용하여
상단 40%에 이미지를, 하단 60%에 타이틀과 설명을 배치하는 SVG를 생성합니다.
"""
import os
import traceback
from split_layout_generator import generate_image_text_layout
from dotenv import load_dotenv

def main() -> None:
    """
    이미지-텍스트 40:60 레이아웃 테스트
    """
    # .env 파일이 있으면 환경 변수를 로드합니다
    load_dotenv()
    
    # 픽사베이 API 키 (환경 변수에서 가져오거나 직접 입력)
    pixabay_api_key = os.getenv("PIXABAY_API_KEY", "")
    
    # 출력 디렉토리 생성
    output_dir = "../output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 예제 데이터
    content_items = [
        {
            "number": "1",
            "title": "진실 은폐 의혹",
            "description": "국정조사 중 진실을 덮고 국민을 속이려 했다는 이유로 고발."
        },
        {
            "number": "2",
            "title": "거짓 공문서 제출",
            "description": "압수·통신 영장 관련 허위 공문서 제출 및 청문회 위증 주장."
        }
    ]
    
    # 타이틀
    title = "⚔️ 여당, 공수처장 검찰 고발! 왜?"
    
    # 이미지는 직접 URL을 제공하거나 픽사베이에서 검색
    image_url = None  # 직접 이미지 URL을 입력하거나 None으로 설정
    pixabay_query = "business celebration success korea"  # 입력한 이미지가 없으면 검색어로 이미지 찾기
    
    # 출력 파일 경로
    output_file = os.path.join(output_dir, "split_layout_test.svg")
    
    try:
        # 40:60 비율의 이미지-텍스트 레이아웃 SVG 생성
        result = generate_image_text_layout(
            title=title,
            content_items=content_items,
            output_file=output_file,
            image_url=image_url,
            pixabay_query=pixabay_query,
            pixabay_api_key=pixabay_api_key,
            width=800,
            height=1000  # 더 긴 세로 형태 (1:1.25 비율)
        )
        
        print(f"이미지-텍스트 40:60 레이아웃 SVG 생성 완료: {result}")
        
        # HTML 테스트 파일 생성
        html_file = os.path.join(output_dir, "split_layout_test.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>40:60 이미지-텍스트 레이아웃 테스트</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        h1 {{
            text-align: center;
            padding: 20px;
            margin: 0;
            background-color: #f0f0f0;
        }}
        .svg-container {{
            width: 100%;
            height: auto;
        }}
        svg {{
            width: 100%;
            height: auto;
            display: block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>40:60 이미지-텍스트 레이아웃</h1>
        <div class="svg-container">
            {open(output_file, 'r', encoding='utf-8').read()}
        </div>
    </div>
</body>
</html>
""")
        print(f"HTML 테스트 파일 생성 완료: {html_file}")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        traceback.print_exc()
    
    print("\n테스트 완료!")

if __name__ == "__main__":
    main() 