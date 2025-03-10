#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
픽사베이 API와 동적 크기 조정 기능을 테스트하는 스크립트입니다.
"""
from typing import List, Dict
import os
import traceback
from card_generator import generate_card_from_data
from dotenv import load_dotenv

def main() -> None:
    """
    픽사베이 API를 사용하여 이미지를 가져오고 
    동적 크기 조정이 가능한 카드 다이어그램을 생성합니다.
    """
    # .env 파일이 있으면 환경 변수를 로드합니다
    load_dotenv()
    
    # 픽사베이 API 키 (환경 변수에서 가져오거나 직접 입력)
    pixabay_api_key = os.getenv("PIXABAY_API_KEY", "")
    
    if not pixabay_api_key:
        print("경고: 픽사베이 API 키가 설정되지 않았습니다. 헤더 이미지 없이 생성됩니다.")
    
    # 출력 디렉토리 생성
    output_dir = "../output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 예제 데이터
    example_data = [
        {
            "title": "정치 스캔들: 여야, 서로 고발전! 진실은?",
            "content": "윤 대통령 구속 과정 둘러싼 여야의 첨예한 대립! 누가 진실을 은폐하고 있을까요? 지금 바로 스크롤하여 확인하세요!"
        },
        {
            "title": "여당 주장",
            "content": "심우정 검찰총장이 관련 혐의를 조작했다는 주장! '증거 없는 기소'로 정쟁에 이용했다는 비판이 나오고 있습니다."
        },
        {
            "title": "야당 주장",
            "content": "내란 수괴 윤석열 구속 과정에 외압이 있었다는 의혹! 검찰총장을 공수처에 고발하며 진상규명을 요구하고 있습니다."
        },
        {
            "title": "국민 반응",
            "content": "SNS와 여론조사에서는 '정치권 싸움에 지친다'는 반응이 지배적. 진실 규명보다 민생을 우선해야 한다는 목소리가 높습니다."
        }
    ]
    
    # 픽사베이 검색어 설정
    pixabay_query = "protest people korea"
    
    # 구조화된 데이터로 다이어그램 생성
    output_file = os.path.join(output_dir, "pixabay_responsive_card.svg")
    
    try:
        result = generate_card_from_data(
            example_data, 
            output_file, 
            title="🚨 정치 스캔들: 여야, 서로 고발전! 진실은?",
            card_color="#E8F4F9",    # 연한 파란색
            title_color="#21364b",   # 짙은 파란색
            content_color="#333333", # 검정색
            background_color="#21364b",  # 짙은 파란색 배경
            pixabay_query=pixabay_query,
            pixabay_api_key=pixabay_api_key,
            header_image_height=300,
            header_color="#FFFFFF",   # 흰색 제목
            size=800,  # 1:1 비율 정사각형
            add_responsive=True
        )
        print(f"픽사베이 이미지와 동적 크기 조정이 적용된 카드 다이어그램 생성 완료: {result}")
        
        # HTML 포장 파일 생성 (테스트 목적)
        html_file = os.path.join(output_dir, "responsive_test.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>반응형 SVG 카드 다이어그램 테스트</title>
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
            border: 1px solid #ddd;
            background-color: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        h1 {{
            text-align: center;
            color: #333;
        }}
        p {{
            text-align: center;
            color: #666;
            margin-bottom: 20px;
        }}
        .resizable-container {{
            width: 100%;
            height: 0;
            padding-bottom: 100%; /* 1:1 비율 유지 */
            position: relative;
            overflow: hidden;
            border: 1px solid #ddd;
            box-sizing: border-box;
        }}
        .svg-wrapper {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }}
        .controls {{
            margin: 20px 0;
            text-align: center;
        }}
        .controls button {{
            padding: 8px 15px;
            margin: 0 5px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        .controls button:hover {{
            background-color: #45a049;
        }}
        /* 다양한 기기에서의 반응형 설정 */
        @media (max-width: 600px) {{
            .container {{
                padding: 10px;
            }}
            h1 {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>반응형 SVG 카드 다이어그램</h1>
        <p>브라우저 크기를 조절하거나 아래 버튼으로 컨테이너 크기를 변경해보세요.</p>
        
        <div class="controls">
            <button onclick="resize(50)">50%</button>
            <button onclick="resize(75)">75%</button>
            <button onclick="resize(100)">100%</button>
        </div>
        
        <div class="resizable-container" id="container">
            <div class="svg-wrapper">
                {open(output_file, 'r', encoding='utf-8').read()}
            </div>
        </div>
    </div>
    
    <script>
        function resize(percent) {{
            document.getElementById('container').style.width = percent + '%';
            document.getElementById('container').style.paddingBottom = percent + '%';
        }}
        
        // 페이지 로드 시 SVG 크기 최적화
        window.addEventListener('load', function() {{
            // SVG가 로드될 때 적절한 크기로 조정
            const svgElements = document.querySelectorAll('svg');
            svgElements.forEach(function(svg) {{
                // SVG에 viewBox가 있는지 확인
                if (!svg.getAttribute('viewBox') && 
                    svg.getAttribute('width') && 
                    svg.getAttribute('height')) {{
                    // viewBox 속성 추가
                    const width = svg.getAttribute('width');
                    const height = svg.getAttribute('height');
                    svg.setAttribute('viewBox', `0 0 ${{width.replace('px', '')}} ${{height.replace('px', '')}}`);
                }}
                
                // 반응형 속성 추가
                svg.setAttribute('width', '100%');
                svg.setAttribute('height', '100%');
                svg.style.display = 'block';
            }});
        }});
    </script>
</body>
</html>
""")
        print(f"HTML 테스트 파일 생성 완료: {html_file}")
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        traceback.print_exc()
    
    print("\n다이어그램 생성 완료!")

if __name__ == "__main__":
    main() 