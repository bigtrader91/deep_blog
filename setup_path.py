"""
PYTHONPATH 설정을 위한 스크립트

이 스크립트는 프로젝트 루트 디렉토리를 Python 경로에 추가합니다.
다음과 같이 사용하세요:

1. 단독 실행 시:
   python setup_path.py

2. 다른 스크립트에서 import 시:
   import setup_path
"""

import os
import sys

# 프로젝트 루트 디렉토리를 가져옵니다
project_root = os.path.dirname(os.path.abspath(__file__))

# 프로젝트 루트가 이미 Python 경로에 있는지 확인합니다
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Python 경로에 추가됨: {project_root}")
else:
    print(f"이미 Python 경로에 존재함: {project_root}")

if __name__ == "__main__":
    print("Python 경로:")
    for path in sys.path:
        print(f"  - {path}")