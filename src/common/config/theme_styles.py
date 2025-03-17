"""
테마 및 스타일 정의 모듈.
마크다운 변환기에서 사용되는 테마와 스타일을 정의합니다.
"""

from enum import Enum
from typing import Dict, Any

class Theme(str, Enum):
    """문서 테마 유형 정의."""
    PURPLE = "purple"
    GREEN = "green"
    BLUE = "blue"
    ORANGE = "orange"
    RED = "red"
    DARK = "dark"
    TEAL = "teal"
    PINK = "pink"

THEME_STYLES: Dict[Theme, Dict[str, str]] = {
    Theme.PURPLE: {
        "h1": "font-size: 2.2rem; font-weight: 700; color: #4a148c; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-bottom: 3px solid #7b1fa2; padding-bottom: 0.3em; font-family: 'Noto Sans KR', sans-serif;",
        "h2": "font-size: 1.8rem; font-weight: 700; color: #4a148c; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-left: 5px solid #9c27b0; padding-left: 0.8em; font-family: 'Noto Sans KR', sans-serif;",
        "h3": "font-size: 1.5rem; font-weight: 700; color: #ffffff; background-color: #6a1b9a; padding: 0.5em 1em; border-radius: 4px; width: 100%; box-sizing: border-box; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-family: 'Noto Sans KR', sans-serif;",
        "h4": "font-size: 1.2rem; font-weight: 700; color: #8e24aa; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-style: italic; font-family: 'Noto Sans KR', sans-serif;",
        "p": "font-size: 1rem; line-height: 1.8; margin-bottom: 1.2em; color: #333; font-family: 'Noto Sans KR', sans-serif;",
        "strong": "font-weight: 700; color: #6a1b9a; font-family: 'Noto Sans KR', sans-serif;",
        "b": "font-weight: 700; color: #8e24aa; font-family: 'Noto Sans KR', sans-serif;",
        "blockquote": "border-left: 4px solid #9c27b0; padding: 0.5em 1em; margin: 1.5em 0; font-style: italic; color: #6a1b9a; background-color: #f9f2ff; font-family: 'Noto Sans KR', sans-serif;",
        "table_header": "border: 1px solid #e1bee7; padding: 0.5em; text-align: left; background-color: #9c27b0; color: white; font-weight: 700;",
        "table_cell": "border: 1px solid #e1bee7; padding: 0.5em; text-align: left;",
        "toc": "background: linear-gradient(135deg, #f5f0ff, #f0e6ff); border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 10px rgba(106, 27, 154, 0.08); font-family: 'Noto Sans KR', sans-serif; border-left: 4px solid #9c27b0;",
        "toc_title": "font-weight: 700; color: #4a148c; font-size: 18px; margin: 0;",
        "toc_link": "color: #6a1b9a; text-decoration: none; font-weight: 500;",
        "list_marker": "display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #9c27b0; margin-right: 10px; position: absolute; left: -20px; top: 8px;",
        "accent_color": "#9c27b0",
        "accent_bg": "#f5f0ff"
    },
    Theme.GREEN: {
        "h1": "font-size: 2.2rem; font-weight: 700; color: #1b5e20; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-bottom: 3px solid #388e3c; padding-bottom: 0.3em; font-family: 'Noto Sans KR', sans-serif;",
        "h2": "font-size: 1.8rem; font-weight: 700; color: #1b5e20; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-left: 5px solid #4caf50; padding-left: 0.8em; font-family: 'Noto Sans KR', sans-serif;",
        "h3": "font-size: 1.5rem; font-weight: 700; color: #ffffff; background-color: #2e7d32; padding: 0.5em 1em; border-radius: 4px; width: 100%; box-sizing: border-box; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-family: 'Noto Sans KR', sans-serif;",
        "h4": "font-size: 1.2rem; font-weight: 700; color: #43a047; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-style: italic; font-family: 'Noto Sans KR', sans-serif;",
        "p": "font-size: 1rem; line-height: 1.8; margin-bottom: 1.2em; color: #333; font-family: 'Noto Sans KR', sans-serif;",
        "strong": "font-weight: 700; color: #2e7d32; font-family: 'Noto Sans KR', sans-serif;",
        "b": "font-weight: 700; color: #43a047; font-family: 'Noto Sans KR', sans-serif;",
        "blockquote": "border-left: 4px solid #4caf50; padding: 0.5em 1em; margin: 1.5em 0; font-style: italic; color: #2e7d32; background-color: #e8f5e9; font-family: 'Noto Sans KR', sans-serif;",
        "table_header": "border: 1px solid #c8e6c9; padding: 0.5em; text-align: left; background-color: #4caf50; color: white; font-weight: 700;",
        "table_cell": "border: 1px solid #c8e6c9; padding: 0.5em; text-align: left;",
        "toc": "background: linear-gradient(135deg, #e8f5e9, #c8e6c9); border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 10px rgba(46, 125, 50, 0.08); font-family: 'Noto Sans KR', sans-serif; border-left: 4px solid #4caf50;",
        "toc_title": "font-weight: 700; color: #1b5e20; font-size: 18px; margin: 0;",
        "toc_link": "color: #2e7d32; text-decoration: none; font-weight: 500;",
        "list_marker": "display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #4caf50; margin-right: 10px; position: absolute; left: -20px; top: 8px;",
        "accent_color": "#4caf50",
        "accent_bg": "#e8f5e9"
    },
    Theme.BLUE: {
        "h1": "font-size: 2.2rem; font-weight: 700; color: #0d47a1; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-bottom: 3px solid #1976d2; padding-bottom: 0.3em; font-family: 'Noto Sans KR', sans-serif;",
        "h2": "font-size: 1.8rem; font-weight: 700; color: #0d47a1; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-left: 5px solid #2196f3; padding-left: 0.8em; font-family: 'Noto Sans KR', sans-serif;",
        "h3": "font-size: 1.5rem; font-weight: 700; color: #ffffff; background-color: #1565c0; padding: 0.5em 1em; border-radius: 4px; width: 100%; box-sizing: border-box; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-family: 'Noto Sans KR', sans-serif;",
        "h4": "font-size: 1.2rem; font-weight: 700; color: #1e88e5; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-style: italic; font-family: 'Noto Sans KR', sans-serif;",
        "p": "font-size: 1rem; line-height: 1.8; margin-bottom: 1.2em; color: #333; font-family: 'Noto Sans KR', sans-serif;",
        "strong": "font-weight: 700; color: #1565c0; font-family: 'Noto Sans KR', sans-serif;",
        "b": "font-weight: 700; color: #1e88e5; font-family: 'Noto Sans KR', sans-serif;",
        "blockquote": "border-left: 4px solid #2196f3; padding: 0.5em 1em; margin: 1.5em 0; font-style: italic; color: #1565c0; background-color: #e3f2fd; font-family: 'Noto Sans KR', sans-serif;",
        "table_header": "border: 1px solid #bbdefb; padding: 0.5em; text-align: left; background-color: #2196f3; color: white; font-weight: 700;",
        "table_cell": "border: 1px solid #bbdefb; padding: 0.5em; text-align: left;",
        "toc": "background: linear-gradient(135deg, #e3f2fd, #bbdefb); border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 10px rgba(21, 101, 192, 0.08); font-family: 'Noto Sans KR', sans-serif; border-left: 4px solid #2196f3;",
        "toc_title": "font-weight: 700; color: #0d47a1; font-size: 18px; margin: 0;",
        "toc_link": "color: #1565c0; text-decoration: none; font-weight: 500;",
        "list_marker": "display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #2196f3; margin-right: 10px; position: absolute; left: -20px; top: 8px;",
        "accent_color": "#2196f3",
        "accent_bg": "#e3f2fd"
    },
    Theme.ORANGE: {
        "h1": "font-size: 2.2rem; font-weight: 700; color: #e65100; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-bottom: 3px solid #ef6c00; padding-bottom: 0.3em; font-family: 'Noto Sans KR', sans-serif;",
        "h2": "font-size: 1.8rem; font-weight: 700; color: #e65100; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-left: 5px solid #ff9800; padding-left: 0.8em; font-family: 'Noto Sans KR', sans-serif;",
        "h3": "font-size: 1.5rem; font-weight: 700; color: #ffffff; background-color: #ef6c00; padding: 0.5em 1em; border-radius: 4px; width: 100%; box-sizing: border-box; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-family: 'Noto Sans KR', sans-serif;",
        "h4": "font-size: 1.2rem; font-weight: 700; color: #f57c00; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-style: italic; font-family: 'Noto Sans KR', sans-serif;",
        "p": "font-size: 1rem; line-height: 1.8; margin-bottom: 1.2em; color: #333; font-family: 'Noto Sans KR', sans-serif;",
        "strong": "font-weight: 700; color: #ef6c00; font-family: 'Noto Sans KR', sans-serif;",
        "b": "font-weight: 700; color: #f57c00; font-family: 'Noto Sans KR', sans-serif;",
        "blockquote": "border-left: 4px solid #ff9800; padding: 0.5em 1em; margin: 1.5em 0; font-style: italic; color: #ef6c00; background-color: #fff3e0; font-family: 'Noto Sans KR', sans-serif;",
        "table_header": "border: 1px solid #ffe0b2; padding: 0.5em; text-align: left; background-color: #ff9800; color: white; font-weight: 700;",
        "table_cell": "border: 1px solid #ffe0b2; padding: 0.5em; text-align: left;",
        "toc": "background: linear-gradient(135deg, #fff3e0, #ffe0b2); border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 10px rgba(239, 108, 0, 0.08); font-family: 'Noto Sans KR', sans-serif; border-left: 4px solid #ff9800;",
        "toc_title": "font-weight: 700; color: #e65100; font-size: 18px; margin: 0;",
        "toc_link": "color: #ef6c00; text-decoration: none; font-weight: 500;",
        "list_marker": "display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #ff9800; margin-right: 10px; position: absolute; left: -20px; top: 8px;",
        "accent_color": "#ff9800",
        "accent_bg": "#fff3e0"
    },
    Theme.RED: {
        "h1": "font-size: 2.2rem; font-weight: 700; color: #b71c1c; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-bottom: 3px solid #c62828; padding-bottom: 0.3em; font-family: 'Noto Sans KR', sans-serif;",
        "h2": "font-size: 1.8rem; font-weight: 700; color: #b71c1c; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-left: 5px solid #f44336; padding-left: 0.8em; font-family: 'Noto Sans KR', sans-serif;",
        "h3": "font-size: 1.5rem; font-weight: 700; color: #ffffff; background-color: #c62828; padding: 0.5em 1em; border-radius: 4px; width: 100%; box-sizing: border-box; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-family: 'Noto Sans KR', sans-serif;",
        "h4": "font-size: 1.2rem; font-weight: 700; color: #d32f2f; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-style: italic; font-family: 'Noto Sans KR', sans-serif;",
        "p": "font-size: 1rem; line-height: 1.8; margin-bottom: 1.2em; color: #333; font-family: 'Noto Sans KR', sans-serif;",
        "strong": "font-weight: 700; color: #c62828; font-family: 'Noto Sans KR', sans-serif;",
        "b": "font-weight: 700; color: #d32f2f; font-family: 'Noto Sans KR', sans-serif;",
        "blockquote": "border-left: 4px solid #f44336; padding: 0.5em 1em; margin: 1.5em 0; font-style: italic; color: #c62828; background-color: #ffebee; font-family: 'Noto Sans KR', sans-serif;",
        "table_header": "border: 1px solid #ffcdd2; padding: 0.5em; text-align: left; background-color: #f44336; color: white; font-weight: 700;",
        "table_cell": "border: 1px solid #ffcdd2; padding: 0.5em; text-align: left;",
        "toc": "background: linear-gradient(135deg, #ffebee, #ffcdd2); border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 10px rgba(198, 40, 40, 0.08); font-family: 'Noto Sans KR', sans-serif; border-left: 4px solid #f44336;",
        "toc_title": "font-weight: 700; color: #b71c1c; font-size: 18px; margin: 0;",
        "toc_link": "color: #c62828; text-decoration: none; font-weight: 500;",
        "list_marker": "display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #f44336; margin-right: 10px; position: absolute; left: -20px; top: 8px;",
        "accent_color": "#f44336",
        "accent_bg": "#ffebee"
    },
    Theme.DARK: {
        "h1": "font-size: 2.2rem; font-weight: 700; color: #ffffff; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-bottom: 3px solid #424242; padding-bottom: 0.3em; font-family: 'Noto Sans KR', sans-serif;",
        "h2": "font-size: 1.8rem; font-weight: 700; color: #ffffff; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-left: 5px solid #757575; padding-left: 0.8em; font-family: 'Noto Sans KR', sans-serif;",
        "h3": "font-size: 1.5rem; font-weight: 700; color: #121212; background-color: #bbbbbb; padding: 0.5em 1em; border-radius: 4px; width: 100%; box-sizing: border-box; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-family: 'Noto Sans KR', sans-serif;",
        "h4": "font-size: 1.2rem; font-weight: 700; color: #e0e0e0; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-style: italic; font-family: 'Noto Sans KR', sans-serif;",
        "p": "font-size: 1rem; line-height: 1.8; margin-bottom: 1.2em; color: #e0e0e0; font-family: 'Noto Sans KR', sans-serif;",
        "strong": "font-weight: 700; color: #ffffff; font-family: 'Noto Sans KR', sans-serif;",
        "b": "font-weight: 700; color: #e0e0e0; font-family: 'Noto Sans KR', sans-serif;",
        "blockquote": "border-left: 4px solid #757575; padding: 0.5em 1em; margin: 1.5em 0; font-style: italic; color: #bbbbbb; background-color: #212121; font-family: 'Noto Sans KR', sans-serif;",
        "table_header": "border: 1px solid #424242; padding: 0.5em; text-align: left; background-color: #212121; color: white; font-weight: 700;",
        "table_cell": "border: 1px solid #424242; padding: 0.5em; text-align: left; color: #e0e0e0;",
        "toc": "background: linear-gradient(135deg, #212121, #1a1a1a); border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3); font-family: 'Noto Sans KR', sans-serif; border-left: 4px solid #757575;",
        "toc_title": "font-weight: 700; color: #ffffff; font-size: 18px; margin: 0;",
        "toc_link": "color: #e0e0e0; text-decoration: none; font-weight: 500;",
        "list_marker": "display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #757575; margin-right: 10px; position: absolute; left: -20px; top: 8px;",
        "accent_color": "#757575",
        "accent_bg": "#212121"
    },
    Theme.TEAL: {
        "h1": "font-size: 2.2rem; font-weight: 700; color: #004d40; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-bottom: 3px solid #00796b; padding-bottom: 0.3em; font-family: 'Noto Sans KR', sans-serif;",
        "h2": "font-size: 1.8rem; font-weight: 700; color: #004d40; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-left: 5px solid #009688; padding-left: 0.8em; font-family: 'Noto Sans KR', sans-serif;",
        "h3": "font-size: 1.5rem; font-weight: 700; color: #ffffff; background-color: #00796b; padding: 0.5em 1em; border-radius: 4px; width: 100%; box-sizing: border-box; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-family: 'Noto Sans KR', sans-serif;",
        "h4": "font-size: 1.2rem; font-weight: 700; color: #00897b; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-style: italic; font-family: 'Noto Sans KR', sans-serif;",
        "p": "font-size: 1rem; line-height: 1.8; margin-bottom: 1.2em; color: #333; font-family: 'Noto Sans KR', sans-serif;",
        "strong": "font-weight: 700; color: #00796b; font-family: 'Noto Sans KR', sans-serif;",
        "b": "font-weight: 700; color: #00897b; font-family: 'Noto Sans KR', sans-serif;",
        "blockquote": "border-left: 4px solid #009688; padding: 0.5em 1em; margin: 1.5em 0; font-style: italic; color: #00796b; background-color: #e0f2f1; font-family: 'Noto Sans KR', sans-serif;",
        "table_header": "border: 1px solid #b2dfdb; padding: 0.5em; text-align: left; background-color: #009688; color: white; font-weight: 700;",
        "table_cell": "border: 1px solid #b2dfdb; padding: 0.5em; text-align: left;",
        "toc": "background: linear-gradient(135deg, #e0f2f1, #b2dfdb); border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 10px rgba(0, 121, 107, 0.08); font-family: 'Noto Sans KR', sans-serif; border-left: 4px solid #009688;",
        "toc_title": "font-weight: 700; color: #004d40; font-size: 18px; margin: 0;",
        "toc_link": "color: #00796b; text-decoration: none; font-weight: 500;",
        "list_marker": "display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #009688; margin-right: 10px; position: absolute; left: -20px; top: 8px;",
        "accent_color": "#009688",
        "accent_bg": "#e0f2f1"
    },
    Theme.PINK: {
        "h1": "font-size: 2.2rem; font-weight: 700; color: #880e4f; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-bottom: 3px solid #ad1457; padding-bottom: 0.3em; font-family: 'Noto Sans KR', sans-serif;",
        "h2": "font-size: 1.8rem; font-weight: 700; color: #880e4f; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-left: 5px solid #d81b60; padding-left: 0.8em; font-family: 'Noto Sans KR', sans-serif;",
        "h3": "font-size: 1.5rem; font-weight: 700; color: #ffffff; background-color: #ad1457; padding: 0.5em 1em; border-radius: 4px; width: 100%; box-sizing: border-box; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-family: 'Noto Sans KR', sans-serif;",
        "h4": "font-size: 1.2rem; font-weight: 700; color: #c2185b; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-style: italic; font-family: 'Noto Sans KR', sans-serif;",
        "p": "font-size: 1rem; line-height: 1.8; margin-bottom: 1.2em; color: #333; font-family: 'Noto Sans KR', sans-serif;",
        "strong": "font-weight: 700; color: #ad1457; font-family: 'Noto Sans KR', sans-serif;",
        "b": "font-weight: 700; color: #c2185b; font-family: 'Noto Sans KR', sans-serif;",
        "blockquote": "border-left: 4px solid #ec407a; padding: 0.5em 1em; margin: 1.5em 0; font-style: italic; color: #ad1457; background-color: #fce4ec; font-family: 'Noto Sans KR', sans-serif;",
        "table_header": "border: 1px solid #f8bbd0; padding: 0.5em; text-align: left; background-color: #ec407a; color: white; font-weight: 700;",
        "table_cell": "border: 1px solid #f8bbd0; padding: 0.5em; text-align: left;",
        "toc": "background: linear-gradient(135deg, #fce4ec, #f8bbd0); border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 10px rgba(173, 20, 87, 0.08); font-family: 'Noto Sans KR', sans-serif; border-left: 4px solid #ec407a;",
        "toc_title": "font-weight: 700; color: #880e4f; font-size: 18px; margin: 0;",
        "toc_link": "color: #ad1457; text-decoration: none; font-weight: 500;",
        "list_marker": "display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #ec407a; margin-right: 10px; position: absolute; left: -20px; top: 8px;",
        "accent_color": "#ec407a",
        "accent_bg": "#fce4ec"
    },
} 