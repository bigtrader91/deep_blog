"""블로그 관련 설정을 정의합니다."""

from dataclasses import dataclass
from .base import BaseConfiguration

BLOG_STRUCTURE_TEMPLATE = """Use the following structure to write a blog post (Answer in Korean):

1. Introduction
   - Include an engaging hook to capture reader attention.
   - Briefly introduce the blog topic (no research required).

2. Main Body Sections (Total of 7 sections)
   - Each section should focus on a sub-topic of the main topic.
   - Write at least 200 characters per section.
   - Include a table in the second and fifth sections.
   - Include a list in the third and sixth sections.
   - Include FAQ in the seventh section.
   - FAQ should be in the following format:

3. Conclusion
   - Summarize the key message from the main content naturally.
   - Emphasize key points to ensure readers remember them.
   - Provide a simple action point (something readers can actually do).
   - Add tags to the end of the blog post.
""" 


@dataclass(kw_only=True)
class BlogConfiguration(BaseConfiguration):
    """블로그 생성 관련 설정"""
    
    blog_structure: str = BLOG_STRUCTURE_TEMPLATE  # 기본 블로그 구조 템플릿

