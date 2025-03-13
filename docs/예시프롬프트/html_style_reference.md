보라색 미래 테마 (Purple Future Theme) 사용 가이드
===============================================

이 가이드는 blog_style_guide.html 파일에 포함된 블로그 스타일링 요소들의 사용법을 설명합니다. 
테마는 보라색을 기반으로 한 미래적인 디자인을 제공하며, 다양한 콘텐츠 요소를 시각적으로 구분하여 가독성을 높입니다.

목차
----
1. 기본 구조
2. 제목 스타일
3. 텍스트 스타일
4. 목록 스타일
5. 강조 요소
6. 특수 컨테이너
7. 코드 표시
8. 테이블
9. 기타 요소
10. 전체 페이지 구성 예시

1. 기본 구조
-----------
블로그 포스트는 다음과 같은 기본 구조를 따릅니다:

1. 메인 제목 (H1)
2. 목차 섹션
3. 주요 섹션 제목 (H2)
4. 본문 내용
5. 하위 섹션 (H3, H4)
6. 필요시 특수 컨테이너 (인용구, 경고 박스 등)

**마크다운 언어 사용은 지침과 충돌로 인해 엄격하게 제한합니다**
#제목
##부제목
###소제목
**강조**
포함 모든 마크다운 언어
다른것보다 강조 부분이 간혈적으로 발생합니다.
**강조** 형식은 `blog_style_guide.md`파일과 `html_style_reference.md`의 강조 부분으로 작성합니다.

2. 제목 스타일
------------
[메인 제목 (H1)]
메인 제목은 페이지의 가장 상단에 위치하며, 블로그 포스트의 주제를 나타냅니다.
<h1 style="font-size: 2.2rem; font-weight: 700; color: #4a148c; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-bottom: 3px solid #7b1fa2; padding-bottom: 0.3em; font-family: 'Noto Sans KR', sans-serif;">블로그 메인 제목</h1>

[주요 섹션 제목 (H2)]
주요 섹션의 시작을 나타내며, 왼쪽에 보라색 세로선이 특징입니다.
<h2 style="font-size: 1.8rem; font-weight: 700; color: #4a148c; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-left: 5px solid #9c27b0; padding-left: 0.8em; font-family: 'Noto Sans KR', sans-serif;">주요 섹션 제목</h2>

[섹션 내 하위 주제 (H3)]
색상이 반전된 스타일로 시각적 계층을 명확히 보여줍니다.
<h3 style="font-size: 1.5rem; font-weight: 700; color: #ffffff; background-color: #6a1b9a; padding: 0.5em 1em; border-radius: 4px; width: 100%; box-sizing: border-box; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-family: 'Noto Sans KR', sans-serif;">섹션 내 하위 주제</h3>

[일반 소제목 (H4)]
이탤릭체가 적용된 보라색 소제목으로, 작은 주제 구분에 사용합니다.
<h4 style="font-size: 1.2rem; font-weight: 700; color: #8e24aa; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-style: italic; font-family: 'Noto Sans KR', sans-serif;">일반 소제목</h4>

3. 텍스트 스타일
--------------
[일반 본문 텍스트]
기본 텍스트 스타일입니다.
<p style="font-size: 1rem; line-height: 1.8; margin-bottom: 1.2em; color: #333; font-family: 'Noto Sans KR', sans-serif;">일반 본문 텍스트입니다.</p>

[강조 텍스트]
보라색으로 강조된 텍스트입니다.
<p style="font-size: 1rem; line-height: 1.8; margin-bottom: 1.2em; color: #6a1b9a; font-weight: 500; font-family: 'Noto Sans KR', sans-serif;">강조가 필요한 본문 텍스트입니다.</p>

[인라인 강조]
특정 단어나 구문을 강조할 때 사용합니다.
<strong style="font-weight: 700; color: #6a1b9a; font-family: 'Noto Sans KR', sans-serif;">특별히 강조하고 싶은 부분</strong>

[굵은 텍스트]
<b style="font-weight: 700; color: #8e24aa; font-family: 'Noto Sans KR', sans-serif;">굵게 처리할 부분</b>

[하이라이트/형광펜 효과]
<mark style="background-color: #e1bee7; color: #6a1b9a; padding: 0 3px; border-radius: 2px; font-family: 'Noto Sans KR', sans-serif;">특별히 강조하고 싶은 부분</mark>

4. 목록 스타일
------------

[체크리스트]
할 일 목록이나 단계별 가이드에 적합합니다.
<ul style="margin-bottom: 1.2em; padding-left: 0.5em; list-style-type: none; color: #333; font-family: 'Noto Sans KR', sans-serif;">
  <li style="margin-bottom: 0.5em; position: relative; padding-left: 2em;">
    <input type="checkbox" id="check1" checked style="position: absolute; left: 0; top: 0.3em; accent-color: #9c27b0;">
    <label for="check1" style="cursor: pointer;">완료된 체크리스트 항목</label>
  </li>
</ul>

5. 강조 요소
-----------
[인용구 스타일]
<blockquote style="border-left: 4px solid #9c27b0; padding: 0.5em 1em; margin: 1.5em 0; font-style: italic; color: #6a1b9a; background-color: #f9f2ff; font-family: 'Noto Sans KR', sans-serif;">
  인용 내용을 여기에 작성합니다.
</blockquote>

8. 테이블
--------
<table style="width: 100%; border-collapse: collapse; margin: 1.5em 0; font-family: 'Noto Sans KR', sans-serif;">
  <thead>
    <tr>
      <th style="border: 1px solid #e1bee7; padding: 0.5em; text-align: left; background-color: #9c27b0; color: white; font-weight: 700;">헤더 1</th>
      <th style="border: 1px solid #e1bee7; padding: 0.5em; text-align: left; background-color: #9c27b0; color: white; font-weight: 700;">헤더 2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="border: 1px solid #e1bee7; padding: 0.5em; text-align: left;">데이터 1</td>
      <td style="border: 1px solid #e1bee7; padding: 0.5em; text-align: left;">데이터 2</td>
    </tr>
  </tbody>
</table>
