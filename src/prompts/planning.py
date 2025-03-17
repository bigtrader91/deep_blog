"""
계획 및 구조 관련 프롬프트

이 모듈은 블로그 계획 및 구조 설계에 사용되는 프롬프트 템플릿을 제공합니다.
"""

# 섹션 계획 템플릿
section_planner_instructions = """
당신은 블로그 포스트를 구성하는 전문 작가입니다.
주제: {topic}

이 주제에 대한 정보를 제공하고 독자에게 유용한 블로그 포스트를 작성하기 위해 
{num_sections}개의 핵심 섹션으로 구성된 블로그 포스트 계획을 만들어 주세요.

각 섹션은 다음 필드를 포함해야 합니다:
- name: 섹션 제목
- description: 섹션에서 다룰 내용에 대한 자세한 설명

블로그는 소개/서론과 결론 섹션을 포함해야 합니다.
다른 섹션들은 주제의 다양한 측면을 다루어야 합니다.
""" 