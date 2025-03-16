"""
검색 유틸리티

이 모듈은 웹 검색을 위한 유틸리티 함수를 제공합니다.
"""
import os
import json
import time
import urllib.request
import urllib.parse
import logging
from typing import Dict, Any, Optional, Literal
from datetime import datetime
from dotenv import load_dotenv

# 로깅 설정
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()
