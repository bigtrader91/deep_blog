"""
마크다운 변환기 테스트 예제.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 독립 실행형 앱에서 함수 임포트
from examples.standalone_markdown_app import markdown_to_html

SAMPLE_MARKDOWN = """# 예시 문서 타이틀

## 소개
이 문서는 LangChain과 Python 라이브러리를 활용해
마크다운을 HTML로 변환하는 예시입니다.

## 특징
- LangChain 워크플로우 활용
- LLM을 통한 테마 추천
- 자동 목차 생성
- 스타일링 적용

## 코드 예시
```python
def hello_world():
    print("안녕하세요!")
```

## 결론
이 예제는 마크다운 변환기의 기능을 보여줍니다.

## 결론
이건 두 번째 결론 (중복)
"""

def main():
    """예제 실행 함수"""
    print("마크다운 변환 예제를 실행합니다...")
    
    # 출력 디렉토리 생성
    output_dir = Path(__file__).resolve().parent.parent / "output" / "html"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 각 테마로 변환 테스트
    themes = ["purple", "green"]
    
    for theme in themes:
        output_path = output_dir / f"example_{theme}.html"
        print(f"\n테마 '{theme}'로 변환 중...")
        
        html_result = markdown_to_html(
            SAMPLE_MARKDOWN, 
            theme_name=theme,
            output_path=str(output_path)
        )
        
        print(f"HTML 길이: {len(html_result)} 문자")
        print(f"저장 경로: {output_path}")
    
    print("\n모든 테마 변환 완료!")

if __name__ == "__main__":
    main() 