# 황금키워드탐색기.py
import os
import sys
import time
import re
import math
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from PySide6 import QtWidgets
from gold_keyword_ui import Ui_MainWindow
from PIL import Image, ImageDraw, ImageFont
import requests
import pandas as pd
import signaturehelper
import traceback
import itertools
from datetime import datetime
import textwrap
from PySide6.QtGui import QFont, QFontDatabase, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QLineEdit,
    QVBoxLayout,
    QWidget,
    QMainWindow,
    QTextEdit,
    QProgressBar,
    QTableWidgetItem,
)
from PySide6.QtGui import QFont, QFontDatabase, QTextCursor
from PySide6.QtCore import QDateTime, QDate, QTime, Qt, QThread
from PySide6.QtGui import QIcon, QPixmap

from naver_keywords_collector import 정보성키워드수집, 상품키워드수집, 데이터랩수집, 연관키워드수집, KeywordCollectorWorker
from utils import extract_category_id, create_image_from_text, create_log_file, DocumentCountWorker, ensure_directory, KEYWORD_DIRS
from concurrent.futures import ThreadPoolExecutor
from logger import set_logger  # 로거 설정을 위한 함수만 import
from configparser import ConfigParser

# 전역 로거 인스턴스를 저장할 변수
_logger = None

def get_logger():
    """전역 로거 인스턴스 반환"""
    return _logger

def set_logger(logger):
    """전역 로거 인스턴스 설정"""
    global _logger
    _logger = logger

def create_safe_filename(filename):
    # 특수문자와 공백을 제거하는 정규 표현식
    safe_filename = re.sub('[^a-zA-Z0-9ㄱ-힣]', '', filename)
    return safe_filename

def parse_config(filename):
    config = ConfigParser()
    # UTF-8 인코딩으로 파일 읽기
    with open(filename, 'r', encoding='utf-8') as f:
        config.read_file(f)
    return config

class GoldKeywordApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(GoldKeywordApp, self).__init__(parent)
        self.setupUi(self)

        # 아이콘
        icon = QIcon("황금키워드2.png")
        self.setWindowIcon(icon)

        # 체크박스 액션
        self.checkBox.stateChanged.connect(self.checkBoxState)
        self.checkBox_2.stateChanged.connect(self.checkBoxState2)

        # settings.txt에서 설정 로드
        config = parse_config("settings.txt")
        
        # init
        self.url = None
        self.pages = config.getint('DEFAULT', 'INFO_PAGES', fallback=20)  # 정보성 키워드 크롤링할 페이지 수
        self.datalab_pages = config.getint('DEFAULT', 'DATALAB_PAGES', fallback=25)  # 데이터랩 크롤링할 페이지 수
        self.df = None
        self.filename = None
        self.keyword = None
        self.mode = None  # 'info' 또는 'product'

        # 버튼 연결
        self.collect_info_keywrod_button.clicked.connect(self.on_execute_collect_info_keywords)
        self.collect_product_keywrod_button.clicked.connect(self.on_execute_collect_product_keywords)
        self.generate_image_button.clicked.connect(self.on_execute_generate_image)
        self.search_button.clicked.connect(self.on_execute_search_keywords)
        self.save_button.clicked.connect(self.on_execute_save_keywords)
        self.pushButton.clicked.connect(self.on_execute_related_keyword)

        self.image_id = None
        self.log_list = []
        self.log_limit = 2000
        self.log_widget = QTextEdit()

        self.scrollArea_log.setWidget(self.log_widget)
        self.log_file_path = "log.txt"

        if not os.path.exists(self.log_file_path):
            create_log_file(self.log_file_path)

        # 로거 설정
        set_logger(self.log)

    def log(self, message):
        """로그 메시지를 UI에 표시하고 저장"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message_with_time = f"[{current_time}] {message}"
            
            # 리스트가 너무 길어지면 앞부분 삭제
            if len(self.log_list) > self.log_limit:
                self.log_list = self.log_list[len(self.log_list) - self.log_limit:]
                
            self.log_list.append(log_message_with_time)
            self.log_widget.setText("\n".join(self.log_list))
            self.log_widget.moveCursor(QTextCursor.End)
            
            # 콘솔에도 출력
            print(log_message_with_time)
            
        except Exception as e:
            print(f"Error in log method: {e}")

    def save_log(self):
        try:
            with open("log.txt", "w", encoding='utf-8') as file:
                file.write("\n".join(self.log_list))
        except Exception as e:
            print(f"Error in save_log method: {e}")

    def checkBoxState(self):
        if self.checkBox.isChecked():
            self.log("정보성 키워드에 문서수(비율) 추가 옵션: ON")
        else:
            self.log("정보성 키워드에 문서수(비율) 추가 옵션: OFF")

    def checkBoxState2(self):
        if self.checkBox_2.isChecked():
            self.log("상품 키워드에 문서수(비율) 추가 옵션: ON")
        else:
            self.log("상품 키워드에 문서수(비율) 추가 옵션: OFF")

    def on_execute_related_keyword(self):
        text = self.lineEdit_4.text()
        if not text.strip():
            self.log("연관키워드 검색어가 입력되지 않았습니다.")
            return

        text2 = ''
        textlist = []
        url_keyword = f"https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query={text}"
        http = requests.get(url_keyword)
        html = BeautifulSoup(http.text, 'html.parser')
        result = html.find_all("a", {"class": "keyword"})
        for i in result:
            text2 += i.text.strip() + '\n'
            textlist.append(i.text.strip())

        # 예시로 3개씩 조합
        import itertools
        textlist_combo = list(map(' '.join, itertools.permutations(textlist, 3)))
        for i in textlist_combo:
            text2 += i + '\n'

        self.textEdit.setText(text2)
        self.log(f"검색 연관키워드 수: {len(result)}")

    def on_execute_collect_info_keywords(self):
        """정보성 키워드 수집 실행"""
        try:
            self.mode = 'info'  # 모드 설정
            url = self.lineEdit_3.text().strip()
            if not url:
                self.log("URL이 입력되지 않았습니다.")
                return

            # 작업 스레드 생성
            self.thread = QThread()
            self.worker = KeywordCollectorWorker(url=url, pages=self.pages, mode='info')
            self.worker.moveToThread(self.thread)

            # 시그널 연결
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            
            self.worker.progress.connect(self.log)
            self.worker.error.connect(self.log)
            self.worker.result.connect(self.handle_info_keywords_result)

            # 버튼 비활성화
            self.collect_info_keywrod_button.setEnabled(False)
            self.thread.finished.connect(
                lambda: self.collect_info_keywrod_button.setEnabled(True)
            )

            # 스레드 시작
            self.thread.start()
        except Exception as e:
            self.log(f"에러 발생: {str(e)}")

    def handle_info_keywords_result(self, df_keyword):
        """정보성 키워드 수집 결과 처리"""
        try:
            if self.checkBox.isChecked():
                self.log("정보성 키워드 문서수(비율) 계산 시작...")
                category_id = extract_category_id(self.lineEdit_3.text().strip())
                today = datetime.now().strftime("%Y%m%d")
                
                # 먼저 정보성 키워드 파일 저장
                info_dir = ensure_directory(KEYWORD_DIRS['info'])
                self.filename = os.path.join(info_dir, f"정보성키워드_{category_id}_{today}.xlsx")
                df_keyword.to_excel(self.filename)
                self.log(f"정보성 키워드 저장 완료: {self.filename}")
                
                # 문서수 계산 작업 스레드 생성
                self.doc_thread = QThread()
                self.doc_worker = DocumentCountWorker(
                    df_keyword,
                    filename=self.filename,  # 전체 경로를 포함한 파일명 전달
                    is_info=True
                )
                self.doc_worker.moveToThread(self.doc_thread)

                # 시그널 연결
                self.doc_thread.started.connect(self.doc_worker.run)
                self.doc_worker.finished.connect(self.doc_thread.quit)
                self.doc_worker.finished.connect(self.doc_worker.deleteLater)
                self.doc_thread.finished.connect(self.doc_thread.deleteLater)
                
                self.doc_worker.progress.connect(self.log)
                self.doc_worker.error.connect(self.log)
                self.doc_worker.result.connect(self.handle_document_ratio_result)

                # 스레드 시작
                self.doc_thread.start()
            else:
                self.save_info_keywords(df_keyword)
            
        except Exception as e:
            self.log(f"결과 처리 중 에러 발생: {str(e)}")

    def save_info_keywords(self, df_keyword):
        """정보성 키워드 저장 (문서비율 미포함)"""
        try:
            category_id = extract_category_id(self.lineEdit_3.text().strip())
            today = datetime.now().strftime("%Y%m%d")
            
            # 정보성 키워드 폴더 생성 및 저장
            info_dir = ensure_directory(KEYWORD_DIRS['info'])
            filename = os.path.join(info_dir, f"정보성키워드_{category_id}_{today}.xlsx")
            
            # 원본 데이터 저장
            df_keyword.to_excel(filename)
            self.log(f"파일 저장 완료: {filename}")
            
            # 테이블에 표시 (인덱스를 컬럼으로 변환)
            self.df = df_keyword
            df_display = df_keyword.reset_index()  # 인덱스를 컬럼으로 변환
            display_columns = ["연관키워드", "월간검색수_PC", "월간검색수_모바일", "경쟁정도"]
            df_display = df_display[display_columns].copy()
            self.dataframe_to_tablewidget(df_display, self.tableWidget)
            
        except Exception as e:
            self.log(f"파일 저장 중 에러 발생: {str(e)}")

    def on_execute_collect_product_keywords(self):
        """상품 키워드 수집 실행"""
        try:
            self.mode = 'product'  # 모드 설정
            # 작업 스레드 생성
            self.thread = QThread()
            self.worker = KeywordCollectorWorker(pages=self.datalab_pages, mode='product')
            self.worker.moveToThread(self.thread)

            # 시그널 연결
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            
            self.worker.progress.connect(self.log)
            self.worker.error.connect(self.log)
            self.worker.result.connect(self.handle_product_keywords_result)

            # 버튼 비활성화
            self.collect_product_keywrod_button.setEnabled(False)
            self.thread.finished.connect(
                lambda: self.collect_product_keywrod_button.setEnabled(True)
            )

            # 스레드 시작
            self.thread.start()
        except Exception as e:
            self.log(f"에러 발생: {str(e)}")

    def handle_product_keywords_result(self, result):
        """상품 키워드 수집 결과 처리"""
        try:
            df_keyword, self.filename = result  # filename 저장
            self.df = df_keyword  # df 저장
            
            if self.checkBox_2.isChecked():
                self.log("문서수(비율) 계산 시작...")
                # DocumentCountWorker 생성
                self.doc_thread = QThread()
                self.doc_worker = DocumentCountWorker(
                    df_keyword,
                    filename=os.path.splitext(self.filename)[0],  # .xlsx 확장자 제거
                    is_info=False  # 상품 키워드 모드
                )
                self.doc_worker.moveToThread(self.doc_thread)

                # 시그널 연결
                self.doc_thread.started.connect(self.doc_worker.run)
                self.doc_worker.finished.connect(self.doc_thread.quit)
                self.doc_worker.finished.connect(self.doc_worker.deleteLater)
                self.doc_thread.finished.connect(self.doc_thread.deleteLater)
                
                self.doc_worker.progress.connect(self.log)
                self.doc_worker.error.connect(self.log)
                self.doc_worker.result.connect(self.handle_document_ratio_result)

                # 스레드 시작
                self.doc_thread.start()
            else:
                # 테이블 위젯에 데이터 표시
                df_display = df_keyword.reset_index()  # 인덱스를 컬럼으로 변환
                display_columns = ["연관키워드", "월간검색수_PC", "월간검색수_모바일", "경쟁정도"]
                df_display = df_display[display_columns].copy()
                self.dataframe_to_tablewidget(df_display, self.tableWidget)
                self.log("상품 키워드 작업 완료.")
            
        except Exception as e:
            self.log(f"결과 처리 중 에러 발생: {str(e)}")

    def on_execute_generate_image(self):
        """
        입력 텍스트를 이미지로 변환
        """
        try:
            text = self.lineEdit_2.text()
            if not text.strip():
                self.log("이미지에 사용할 텍스트가 입력되지 않았습니다.")
                return
            img_path = create_image_from_text(text)
            self.log(f"이미지 생성 완료: {img_path}")
        except Exception as e:
            tb = traceback.format_exc()
            self.log(f"이미지 생성 중 에러발생.\n{e}\n{tb}")
            QApplication.processEvents()
            self.save_log()

    def on_execute_search_keywords(self):
        """
        검색창에 입력된 키워드의 연관키워드 조회
        """
        keyword = self.lineEdit.text().strip()
        if not keyword:
            self.log("검색할 키워드가 입력되지 않았습니다.")
            return

        self.keyword = keyword
        df_keyword = 연관키워드수집(keyword)
        
        # 데이터 타입 변환
        df_keyword['월간검색수_PC'] = pd.to_numeric(df_keyword['월간검색수_PC'].replace('< 10', '10'), errors='coerce').fillna(0).astype(int)
        df_keyword['월간검색수_모바일'] = pd.to_numeric(df_keyword['월간검색수_모바일'].replace('< 10', '10'), errors='coerce').fillna(0).astype(int)
        
        # 총조회수 계산
        df_keyword["총조회수"] = df_keyword["월간검색수_PC"] + df_keyword["월간검색수_모바일"]

        # 결과 테이블에 표시할 컬럼 선택
        df_keyword2 = df_keyword[["연관키워드", "월간검색수_PC", "월간검색수_모바일", "경쟁정도", "총조회수"]]
        self.df = df_keyword2
        self.dataframe_to_tablewidget(df_keyword2, self.tableWidget)
        self.log(f"{keyword} 연관키워드 조회 완료. 총 {len(df_keyword2)}개 키워드")

    def on_execute_save_keywords(self):
        """테이블에 있는 키워드를 엑셀로 저장"""
        if self.df is None or self.keyword is None:
            self.log("저장할 키워드 데이터가 없습니다.")
            return
        
        try:
            today = datetime.now().strftime("%Y%m%d")
            
            # 연관 키워드 폴더 생성 및 저장
            related_dir = ensure_directory(KEYWORD_DIRS['related'])
            
            # 파일명 생성 및 저장
            excel_filename = os.path.join(related_dir, f"연관키워드_{self.keyword}_{today}.xlsx")
            self.df.to_excel(excel_filename)
            self.log(f"키워드 저장 완료: {excel_filename}")
            
        except Exception as e:
            self.log(f"파일 저장 중 에러 발생: {str(e)}")

    def dataframe_to_tablewidget(self, df, table_widget):
        table_widget.setRowCount(df.shape[0])
        table_widget.setColumnCount(df.shape[1])
        table_widget.setHorizontalHeaderLabels(df.columns)

        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iat[row, col]))
                table_widget.setItem(row, col, item)

    def on_execute_document_ratio(self):
        """문서 비율 계산 실행"""
        try:
            if self.df is None:
                self.log("먼저 키워드를 수집해주세요.")
                return

            # DocumentCountWorker 생성
            self.worker = DocumentCountWorker(
                self.df, 
                filename=self.filename,
                is_info=self.mode == 'info'  # 정보성 키워드 여부
            )
            self.thread = QThread()
            self.worker.moveToThread(self.thread)
            
            # 시그널 연결
            self.worker.progress.connect(self.log)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.result.connect(self.handle_document_ratio_result)
            self.worker.error.connect(self.log)
            
            # 스레드 시작
            self.thread.start()
            
        except Exception as e:
            self.log(f"문서 비율 계산 중 오류 발생: {str(e)}")

    def handle_document_ratio_result(self, df_result):
        """문서 비율 계산 결과 처리"""
        try:
            # 결과 DataFrame을 테이블에 표시
            self.df = df_result
            
            # 인덱스를 컬럼으로 변환
            df_display = df_result.reset_index()  # 인덱스를 컬럼으로 변환
            
            # 표시할 컬럼 선택 및 정렬
            if self.mode == 'info':
                display_columns = ["연관키워드", "월간검색수_PC", "월간검색수_모바일", "문서수", "비율", "경쟁정도"]
            else:  # product mode
                display_columns = ["연관키워드", "월간검색수_PC", "월간검색수_모바일", "문서수", "비율", "경쟁정도"]
            
            # 필요한 컬럼만 선택 (존재하는 컬럼만)
            available_columns = [col for col in display_columns if col in df_display.columns]
            df_display = df_display[available_columns].copy()
            
            # 비율을 퍼센트로 표시 (비율 컬럼이 있는 경우만)
            if '비율' in df_display.columns:
                df_display['비율'] = df_display['비율'].map('{:.2%}'.format)
            
            # 테이블 위젯에 데이터 표시
            self.dataframe_to_tablewidget(df_display, self.tableWidget)
            
            self.log("문서 비율 계산 결과가 테이블에 업데이트되었습니다.")
            
        except Exception as e:
            self.log(f"결과 처리 중 에러 발생: {str(e)}\n{traceback.format_exc()}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    myWindow = GoldKeywordApp()
    myWindow.show()
    sys.exit(app.exec())

    app = QtWidgets.QApplication(sys.argv)
    myWindow = GoldKeywordApp()
    myWindow.show()
    sys.exit(app.exec())
