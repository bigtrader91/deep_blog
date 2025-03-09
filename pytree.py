import os
import ast
from pathlib import Path

def print_python_tree(directory, exclude_dirs=None, prefix=""):
    """
    주어진 디렉토리 내의 파이썬 파일과 하위 디렉토리를 트리 구조로 출력합니다.
    각 파이썬 파일 내부에 정의된 함수, 비동기 함수, 클래스(내부 메서드 포함)도 함께 출력합니다.
    
    Args:
        directory (str): 검색할 디렉토리 경로
        exclude_dirs (list): 제외할 디렉토리 이름 목록 (예: ['venv', '__pycache__'])
        prefix (str): 트리 구조를 표현하기 위한 접두사
    """
    if exclude_dirs is None:
        exclude_dirs = []
    
    # 디렉토리 경로 객체 생성 및 항목 정렬
    path = Path(directory)
    items = sorted(path.glob("*"))
    
    # 제외할 디렉토리 필터링
    filtered_items = [
        item for item in items 
        if not (item.is_dir() and item.name in exclude_dirs)
    ]
    
    for i, item in enumerate(filtered_items):
        is_last = i == len(filtered_items) - 1
        
        # 현재 항목에 맞는 트리 분기 문자 선택
        current_prefix = "└── " if is_last else "├── "
        # 다음 수준의 들여쓰기를 위한 접두사
        next_prefix = "    " if is_last else "│   "
        
        if item.is_file() and item.suffix == ".py":
            # 파이썬 파일인 경우 파일명 출력
            print(f"{prefix}{current_prefix}{item.name}")
            # 해당 파일 내부의 함수, 클래스 등 분석 후 출력
            # analyze_python_file(item, prefix + next_prefix)
        elif item.is_dir():
            # 디렉토리인 경우 디렉토리명 출력 후 재귀 호출
            print(f"{prefix}{current_prefix}{item.name}/")
            print_python_tree(item, exclude_dirs, prefix + next_prefix)

def analyze_python_file(file_path, prefix=""):
    """
    주어진 파이썬 파일을 파싱하여, 내부에 정의된 함수, 비동기 함수, 클래스(내부 메서드 포함)를 출력합니다.
    
    Args:
        file_path (Path): 분석할 파이썬 파일 경로 (Path 객체)
        prefix (str): 트리 구조 출력 시 사용할 접두사
    """
    try:
        with file_path.open("r", encoding="utf-8") as f:
            file_content = f.read()
        tree = ast.parse(file_content, filename=str(file_path))
    except Exception as e:
        print(f"{prefix}[Error parsing file: {e}]")
        return

    # 모듈 레벨의 정의들을 재귀적으로 출력
    print_definitions(tree, prefix)

def print_definitions(node, prefix, indent="    "):
    """
    AST 노드를 순회하면서 함수, 비동기 함수, 클래스 정의들을 재귀적으로 출력합니다.
    
    Args:
        node (ast.AST): 현재 AST 노드
        prefix (str): 현재 레벨에서 사용할 접두사
        indent (str): 한 단계 들여쓰기할 때 사용할 문자열
    """
    # ast.iter_child_nodes()를 사용해 직접 자식 노드를 순회합니다.
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.FunctionDef):
            print(f"{prefix}Function: {child.name} (line {child.lineno})")
            # 함수 내부에 중첩 정의(내부 함수 등)가 있을 경우 재귀 호출
            print_definitions(child, prefix + indent, indent)
        elif isinstance(child, ast.AsyncFunctionDef):
            print(f"{prefix}Async Function: {child.name} (line {child.lineno})")
            print_definitions(child, prefix + indent, indent)
        elif isinstance(child, ast.ClassDef):
            print(f"{prefix}Class: {child.name} (line {child.lineno})")
            print_definitions(child, prefix + indent, indent)
        # 그 외 노드는 건너뜁니다.

if __name__ == "__main__":
    # 기본적으로 제외할 디렉토리 목록
    default_exclude = ['venv', '__pycache__', '.git', '.idea', 'node_modules', 'docs', 'alembic', '.github','tests', 'pytree.py']
    
    # 현재 디렉토리에서 시작
    current_dir = os.getcwd()
    print(f"Directory: {current_dir}")
    print(f"Excluded directories: {default_exclude}\n")
    print_python_tree(current_dir, exclude_dirs=default_exclude)
    
    # 사용자 정의 제외 디렉토리 예시:
    # custom_exclude = ['venv', 'tests', 'docs']
    # print_python_tree(current_dir, exclude_dirs=custom_exclude)