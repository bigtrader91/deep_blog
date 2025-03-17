"""
로깅 설정 및 유틸리티 함수를 제공합니다.

이 모듈은 애플리케이션 전체에서 일관된 로깅 형식과 구성을 제공합니다.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

# 로그 레벨 매핑
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

# 기본 로그 레벨은 INFO
DEFAULT_LOG_LEVEL = 'info'

# 기본 로그 디렉토리
DEFAULT_LOG_DIR = 'logs'

# 로그 파일 최대 크기 (10MB)
MAX_LOG_SIZE = 10 * 1024 * 1024

# 로그 파일 백업 개수
BACKUP_COUNT = 5

def get_logger(name: str, log_level: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """지정된 이름으로 로거를 생성하고 반환합니다.
    
    Args:
        name (str): 로거 이름 (일반적으로 __name__)
        log_level (str, optional): 로그 레벨 ('debug', 'info', 'warning', 'error', 'critical'). 
                                기본값은 환경 변수 LOG_LEVEL 또는 'info'.
        log_file (str, optional): 로그 파일 경로. 기본값은 None으로, 로그 디렉토리에 자동 생성.
    
    Returns:
        logging.Logger: 설정된 로거 인스턴스
    """
    # 로그 레벨 설정
    log_level = log_level or os.getenv('LOG_LEVEL', DEFAULT_LOG_LEVEL).lower()
    level = LOG_LEVELS.get(log_level, logging.INFO)
    
    # 로거 생성
    logger = logging.getLogger(name)
    
    # 로거가 이미 핸들러를 가지고 있으면 재설정하지 않음
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(console_handler)
    
    # 파일 핸들러 설정 (선택적)
    if log_file or os.getenv('LOG_TO_FILE', 'false').lower() == 'true':
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(log_file) if log_file else DEFAULT_LOG_DIR
        os.makedirs(log_dir, exist_ok=True)
        
        # 로그 파일 경로
        log_path = log_file or os.path.join(log_dir, f"{name.replace('.', '_')}.log")
        
        # 파일 핸들러 생성
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        
        # 파일 핸들러 추가
        logger.addHandler(file_handler)
    
    return logger
