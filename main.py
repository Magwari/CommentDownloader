import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QTextEdit, QComboBox, QDateEdit, QCheckBox,
                             QGroupBox, QGridLayout, QFormLayout, QLineEdit, QScrollArea, QListWidget, QFrame)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QDate, QThread, Signal, QUrl, QObject, Slot
from PySide6.QtGui import QPalette, QFont
import json
from datetime import datetime

import uuid

from comment_downloader.google_search import google_search
from comment_downloader.exportcomments import process_url

# =============================================================================
# [스타일 시트] HTML의 CSS를 PyQt 스타일시트(QSS)로 변환
# =============================================================================
STYLESHEET = """
QMainWindow {
    background-color: #f8fafc;
}
QWidget {
    font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
    color: #1e293b;
    font-size: 14px;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
/* 카드 스타일 컨테이너 */
#MainCard {
    background-color: #ffffff;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
}
/* 헤더 */
QLabel#HeaderTitle {
    font-size: 24px;
    font-weight: bold;
    color: #1e293b;
    padding-bottom: 10px;
    border-bottom: 2px solid #e2e8f0;
}
/* 섹션 박스 */
QGroupBox {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 15px;
    background-color: #f1f5f9;
    font-weight: bold;
    color: #64748b;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    left: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    left: 10px;
}
/* 입력 필드 */
QLineEdit, QComboBox, QDateEdit {
    padding: 8px;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    background-color: white;
    selection-background-color: #2563eb;
    min-width: 200px;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
    border: 2px solid #2563eb;
}
/* 버튼 스타일 */
QPushButton#SubmitBtn {
    background-color: #2563eb;
    color: white;
    font-weight: bold;
    font-size: 16px;
    border-radius: 8px;
    padding: 12px;
    border: none;
}
QPushButton#SubmitBtn:hover {
    background-color: #1d4ed8;
}
QPushButton#SubmitBtn:disabled {
    background-color: #94a3b8;
}
QPushButton#DownloadBtn {
    background-color: #10b981;
    color: white;
    font-weight: bold;
    padding: 12px;
    border-radius: 8px;
    border: none;
}
QPushButton#DownloadBtn:hover {
    background-color: #059669;
}
QPushButton#AddBtn {
    border: 1px dashed #2563eb;
    color: #2563eb;
    background-color: transparent;
    padding: 5px 10px;
    border-radius: 4px;
}
QPushButton#AddBtn:hover {
    background-color: #eff6ff;
}
QPushButton#RemoveBtn {
    color: #ef4444;
    font-weight: bold;
    background: transparent;
    border: none;
}
/* 로그 영역 */
QTextEdit#LogArea {
    background-color: #1e293b;
    color: #e2e8f0;
    border-radius: 8px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 12px;
    padding: 10px;
}
/* 검색 결과 URL 항목 */
QLabel#SearchResultUrl {
    background-color: white;
    padding: 5px;
    border-radius: 4px;
}
"""

class SearchWorker(QObject):
    """검색 작업을 위한 스레드"""
    # 시그널 정의
    start_search = Signal(str, list)
    search_started = Signal(str)
    search_progress = Signal(str)
    search_finished = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.start_search.connect(self.run_search)
    
    @Slot(str, list)
    def run_search(self, query, sites):
        """검색 작업 실행"""
        try:
            self.search_started.emit(f"Google 검색 시작: {query}")
            results = []
            for site in sites:
                googleSearchId = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{datetime.now()}_{site}_{query}"))
                site_results = google_search(query, googleSearchId, site, max_search_num=10)
                results.extend(site_results)
                self.search_progress.emit(f"사이트 {site} 검색 완료: {len(site_results)}개 결과")
            
            self.search_finished.emit([item['link'] for item in results])
        except Exception as e:
            self.error_occurred.emit(f"검색 중 오류 발생: {str(e)}")

class ExportWorker(QObject):
    """댓글 수집 작업을 위한 스레드"""
    # 시그널 정의
    start_export = Signal(list, dict)
    export_started = Signal(str)
    export_progress = Signal(str)
    export_finished = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.start_export.connect(self.run_export) 
    
    @Slot(list)
    def run_export(self, urls, options):
        """댓글 수집 작업 실행"""
        try:
            # 날짜 필터 정보 가져오기
            start_date = datetime.strptime(options['start_date'], "%Y-%m-%d").timestamp()
            end_date = datetime.strptime(options['end_date'], "%Y-%m-%d").timestamp()
            
            self.export_started.emit(f"댓글 수집 시작: {len(urls)}개 URL")
            results = []
            for i, url in enumerate(urls):
                self.export_progress.emit(f"댓글 수집 중: {i+1}/{len(urls)} - {url}")
                try:
                    # 날짜 필터 옵션 추가
                    guid, data = process_url(url)
                    filtered_data = list(filter(lambda x: start_date <= int(x['time']) and end_date >= int(x['time']), data))
                    results.extend(filtered_data)
                    # results.append({
                    #     'url': url,
                    #     'guid': guid,
                    #     'data': data
                    # })
                except Exception as e:
                    self.export_progress.emit(f"오류: {url} - {str(e)}")
                    results.append({
                        'url': url,
                        'error': str(e)
                    })
            
            self.export_finished.emit({'results': results})
        except Exception as e:
            self.error_occurred.emit(f"댓글 수집 중 오류 발생: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("온라인 소비자 리뷰 검색/수집")
        self.setGeometry(100, 100, 1400, 900)
        
        # UI 설정
        self.init_ui()
        
    def init_ui(self):
        # 메인 레이아웃
        main_widget = QWidget()
        main_widget.setObjectName("MainCard")
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        self.setStyleSheet(STYLESHEET)
        
        # 좌측 패널 (입력 폼)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(24, 24, 24, 24)
        
        # 제목
        title_label = QLabel("온라인 소비자 리뷰 검색/수집")
        title_label.setObjectName("HeaderTitle")
        left_layout.addWidget(title_label)
        # 입력 폼 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        
        # 미디어 선택 섹션
        media_group = QGroupBox("Media (플랫폼 선택)")
        media_layout = QHBoxLayout()
        self.media_checkboxes = []
        platforms = ["BestBuy", "Walmart", "Amazon", "Reddit"]
        for platform in platforms:
            checkbox = QCheckBox(platform)
            # Walmart과 Amazon은 선택 불가능하도록 비활성화
            if platform in ["Walmart", "Amazon"]:
                checkbox.setEnabled(False)
                # 비활성화된 체크박스의 텍스트 색상 변경
                checkbox.setStyleSheet("color: #94a3b8;")
            self.media_checkboxes.append(checkbox)
            media_layout.addWidget(checkbox)
        media_group.setLayout(media_layout)
        form_layout.addWidget(media_group)
        
        # 날짜 선택 섹션
        date_group = QGroupBox("Date (기간 설정)")
        date_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date = QDateEdit()
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(QLabel("시작일:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("~"))
        date_layout.addWidget(self.end_date)
        date_group.setLayout(date_layout)
        form_layout.addWidget(date_group)
        
        # 제품 스펙 섹션
        spec_group = QGroupBox("Product Spec (검색어 조건)")
        spec_layout = QVBoxLayout()
        
        # 제품군
        product_layout = QHBoxLayout()
        product_layout.addWidget(QLabel("제품군:"))
        self.product_type_combo = QComboBox()
        self.product_type_combo.addItems(["", "TV", "Monitor", "Smart Phone", "Tablet", "NBPC", "custom"])
        self.product_type_combo.currentTextChanged.connect(self.toggle_product_type_input)
        self.product_type_input = QLineEdit()
        self.product_type_input.setPlaceholderText("제품군 입력")
        self.product_type_input.setEnabled(False)
        product_layout.addWidget(self.product_type_combo)
        product_layout.addWidget(self.product_type_input)
        product_layout.setStretch(0, 1)  # label을 1부분 확장
        product_layout.setStretch(1, 2)  # combo box를 2부분 확장
        product_layout.setStretch(2, 3)  # input을 3부분 확장
        spec_layout.addLayout(product_layout)
        
        # 브랜드
        brand_layout = QHBoxLayout()
        brand_layout.addWidget(QLabel("브랜드:"))
        self.brand_combo = QComboBox()
        self.brand_combo.addItems(["", "LG", "Samsung", "Apple", "custom"])
        self.brand_combo.currentTextChanged.connect(self.toggle_brand_input)
        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("브랜드명 입력")
        self.brand_input.setEnabled(False)
        brand_layout.addWidget(self.brand_combo)
        brand_layout.addWidget(self.brand_input)
        brand_layout.setStretch(0, 1)  # label을 1부분 확장
        brand_layout.setStretch(1, 2)  # combo box를 2부분 확장
        brand_layout.setStretch(2, 3)  # input을 3부분 확장
        spec_layout.addLayout(brand_layout)
        
        # 패널타입
        panel_layout = QHBoxLayout()
        panel_layout.addWidget(QLabel("패널타입:"))
        self.panel_type_combo = QComboBox()
        self.panel_type_combo.addItems(["", "OLED", "LCD", "custom"])
        self.panel_type_combo.currentTextChanged.connect(self.toggle_panel_type_input)
        self.panel_type_input = QLineEdit()
        self.panel_type_input.setPlaceholderText("패널타입 입력")
        self.panel_type_input.setEnabled(False)
        panel_layout.addWidget(self.panel_type_combo)
        panel_layout.addWidget(self.panel_type_input)
        panel_layout.setStretch(0, 1)  # label을 1부분 확장
        panel_layout.setStretch(1, 2)  # combo box를 2부분 확장
        panel_layout.setStretch(2, 3)  # input을 3부분 확장
        spec_layout.addLayout(panel_layout)
        
        # 라인업
        lineup_layout = QHBoxLayout()
        lineup_layout.addWidget(QLabel("라인업 (Series):"))
        self.lineup_input = QLineEdit()
        self.lineup_input.setPlaceholderText("예: G5")
        lineup_layout.addWidget(self.lineup_input)
        lineup_layout.setStretch(0, 1)  # label을 1부분 확장
        lineup_layout.setStretch(1, 3)  # input을 3부분 확장
        spec_layout.addLayout(lineup_layout)
        
        # 해상도
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("해상도:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["", "UHD", "FHD", "custom"])
        self.resolution_combo.currentTextChanged.connect(self.toggle_resolution_input)
        self.resolution_input = QLineEdit()
        self.resolution_input.setPlaceholderText("해상도 입력")
        self.resolution_input.setEnabled(False)
        resolution_layout.addWidget(self.resolution_combo)
        resolution_layout.addWidget(self.resolution_input)
        resolution_layout.setStretch(0, 1)  # label을 1부분 확장
        resolution_layout.setStretch(1, 2)  # combo box를 2부분 확장
        resolution_layout.setStretch(2, 3)  # input을 3부분 확장
        spec_layout.addLayout(resolution_layout)
        
        # 사이즈
        size_group = QGroupBox("사이즈 (중복 선택)")
        size_layout = QHBoxLayout()
        self.size_checkboxes = []
        sizes = ["85", "77", "75", "65", "55", "43"]
        for size in sizes:
            checkbox = QCheckBox(size)
            self.size_checkboxes.append(checkbox)
            size_layout.addWidget(checkbox)
        
        # 직접 입력 체크박스
        custom_size_checkbox = QCheckBox("직접")
        self.size_custom_input = QLineEdit()
        self.size_custom_input.setPlaceholderText("사이즈 입력 (inch)")
        self.size_custom_input.setEnabled(False)
        custom_size_checkbox.checkStateChanged.connect(lambda state: self.toggle_custom_input(self.size_custom_input, state))
        size_layout.addWidget(custom_size_checkbox)
        size_layout.addWidget(self.size_custom_input)
        
        size_group.setLayout(size_layout)
        spec_layout.addWidget(size_group)
        
        # 주사율
        refresh_group = QGroupBox("주사율 (중복 선택)")
        refresh_layout = QHBoxLayout()
        self.refresh_checkboxes = []
        refresh_rates = ["240", "165", "144", "120"]
        for rate in refresh_rates:
            checkbox = QCheckBox(rate + "Hz")
            self.refresh_checkboxes.append(checkbox)
            refresh_layout.addWidget(checkbox)
        
        # 직접 입력 체크박스
        custom_refresh_checkbox = QCheckBox("직접")
        self.refresh_custom_input = QLineEdit()
        self.refresh_custom_input.setPlaceholderText("Hz까지 입력하세요")
        self.refresh_custom_input.setEnabled(False)
        custom_refresh_checkbox.checkStateChanged.connect(lambda state: self.toggle_custom_input(self.refresh_custom_input, state))
        refresh_layout.addWidget(custom_refresh_checkbox)
        refresh_layout.addWidget(self.refresh_custom_input)
        
        refresh_group.setLayout(refresh_layout)
        spec_layout.addWidget(refresh_group)
        
        # 추가 상세 스펙 (동적)
        self.dynamic_specs_container = QVBoxLayout()
        self.dynamic_specs_container.addWidget(QLabel("추가 상세 스펙"))
        self.add_spec_button = QPushButton("+ 항목 추가")
        self.add_spec_button.clicked.connect(self.add_spec_field)
        self.dynamic_specs_container.addWidget(self.add_spec_button)
        
        spec_layout.addLayout(self.dynamic_specs_container)
        spec_group.setLayout(spec_layout)
        form_layout.addWidget(spec_group)
        
        # 검색 대상 URL 섹션
        search_url_group = QGroupBox("🔍 검색 대상 URL")
        search_url_layout = QVBoxLayout()
        search_url_layout.setContentsMargins(10, 10, 10, 10)
        
        # 검색 결과 리스트
        self.search_results_list_container = QVBoxLayout()
        self.search_results_list_container.setSpacing(5)
        self.search_results_list_container.setContentsMargins(0, 0, 0, 0)
        search_url_layout.addLayout(self.search_results_list_container)
        
        # 검색 대상 추가 입력창
        self.search_input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색 대상 URL 입력")
        self.add_search_button = QPushButton("추가")
        self.add_search_button.clicked.connect(self.add_search_url)
        self.search_input_layout.addWidget(self.search_input)
        self.search_input_layout.addWidget(self.add_search_button)
        search_url_layout.addLayout(self.search_input_layout)
        
        search_url_group.setLayout(search_url_layout)
        form_layout.addWidget(search_url_group)
        
        
        # 제출 버튼
        self.submit_button = QPushButton("URL 검색 시작하기")
        self.submit_button.clicked.connect(self.submit_form)
        self.submit_button.setStyleSheet("font-size: 16px; padding: 12px; font-weight: bold;")
        form_layout.addWidget(self.submit_button)
        
        scroll_area.setWidget(form_widget)
        left_layout.addWidget(scroll_area)
        
        # 우측 패널 (로그 및 결과)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 로그 헤더
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("📋 진행 상황"))
        self.status_label = QLabel("대기 중")
        self.status_label.setStyleSheet("color: #64748b; font-size: 14px;")
        log_header.addWidget(self.status_label, alignment=Qt.AlignRight)
        right_layout.addLayout(log_header)
        
        # 로그 컨테이너
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #1e293b; color: #e2e8f0; font-family: 'Consolas', 'Monaco', monospace; font-size: 12px;")
        right_layout.addWidget(self.log_text)
        
        # 검색 결과 표시 영역
        # 기존의 검색 결과 리스트는 제거하고, 새로운 리스트만 사용
        # 검색 결과 표시 영역은 더 이상 필요 없음
        
        # 수집 시작 버튼
        self.export_button = QPushButton("댓글 수집 시작")
        self.export_button.clicked.connect(self.start_export)
        self.export_button.hide()
        self.export_button.setStyleSheet("background-color: #2563eb; color: white; font-size: 14px; padding: 12px; font-weight: bold;")
        right_layout.addWidget(self.export_button)
        
        # 다운로드 버튼
        self.download_button = QPushButton("리뷰 수집 파일 다운로드")
        self.download_button.clicked.connect(self.download_results)
        self.download_button.hide()
        self.download_button.setStyleSheet("background-color: #10b981; color: white; font-size: 14px; padding: 12px; font-weight: bold;")
        right_layout.addWidget(self.download_button)
        
        # 메인 레이아웃에 패널 추가
        main_layout.addWidget(left_panel, 2)
        main_layout.addWidget(right_panel, 1)
        
        # 초기 상태 설정
        self.status_label.setText("대기 중")

    def create_search_worker(self):
        # 검색 작업자 생성
        self.search_worker = SearchWorker()
        self.search_worker.search_started.connect(self.on_search_started)
        self.search_worker.search_progress.connect(self.on_search_progress)
        self.search_worker.search_finished.connect(self.on_search_finished)
        self.search_worker.error_occurred.connect(self.on_error)
        
    def create_export_worker(self):
        # 댓글 수집 작업자 생성
        self.export_worker = ExportWorker()
        self.export_worker.export_started.connect(self.on_export_started)
        self.export_worker.export_progress.connect(self.on_export_progress)
        self.export_worker.export_finished.connect(self.on_export_finished)
        self.export_worker.error_occurred.connect(self.on_error)
        
        # 댓글 수집 완료 후 버튼을 다시 활성화
        self.export_worker.export_finished.connect(self.reset_button_state)
        
    def toggle_product_type_input(self, text):
        self.product_type_input.setEnabled(text == "custom")
        
    def toggle_brand_input(self, text):
        self.brand_input.setEnabled(text == "custom")
        
    def toggle_panel_type_input(self, text):
        self.panel_type_input.setEnabled(text == "custom")
        
    def toggle_resolution_input(self, text):
        self.resolution_input.setEnabled(text == "custom")
        
    def toggle_custom_input(self, input_widget, state):
        input_widget.setEnabled(state == Qt.Checked)
        
    def add_spec_field(self):
        # 동적 스펙 필드 추가 (간단한 구현)
        spec_layout = QHBoxLayout()
        value_input = QLineEdit()
        value_input.setPlaceholderText("값")
        remove_button = QPushButton("×")
        remove_button.setFixedSize(25, 25)
        remove_button.clicked.connect(lambda: self.remove_spec_field(spec_layout))
        
        spec_layout.addWidget(value_input)
        spec_layout.addWidget(remove_button)
        
        self.dynamic_specs_container.insertLayout(self.dynamic_specs_container.count() - 1, spec_layout)
        
    def remove_spec_field(self, layout):
        # 레이아웃 제거
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        layout.setParent(None)
        
    def remove_search_result_item(self, item_widget):
        """검색 결과 항목 삭제"""
        self.search_results_list_container.removeWidget(item_widget)
        item_widget.deleteLater()
        
    def submit_form(self):
        """폼 제출 처리"""
        # 버튼 비활성화
        self.submit_button.setEnabled(False)
        self.submit_button.setText("진행 중...")
        
        # 로그 초기화
        self.log_text.clear()
        self.status_label.setText("처리 중...")
        self.status_label.setStyleSheet("color: #2563eb;")
        self.download_button.hide()
        self.export_button.hide()
        self.clear_search_results_list()
        
        # 입력값 수집
        selected_media = []
        for checkbox in self.media_checkboxes:
            if checkbox.isChecked():
                selected_media.append(checkbox.text())
        
        if not selected_media:
            self.add_log("오류: 최소 하나의 미디어 플랫폼을 선택해야 합니다.", "error")
            self.reset_button_state()
            return
            
        # start_date = self.start_date.date().toString("yyyy-MM-dd")
        # end_date = self.end_date.date().toString("yyyy-MM-dd")
        
        # 스펙 데이터 수집
        spec_data = {}
        keywords = []
        
        # 정적 필드 수집
        if self.product_type_combo.currentText() == "custom":
            product_type = self.product_type_input.text().strip()
        else:
            product_type = self.product_type_combo.currentText()
            
        if product_type:
            spec_data["productType"] = product_type
            keywords.append(f"intitle:{product_type}")
            
        if self.brand_combo.currentText() == "custom":
            brand = self.brand_input.text().strip()
        else:
            brand = self.brand_combo.currentText()
            
        if brand:
            spec_data["brand"] = brand
            keywords.append(f"intitle:{brand}")
            
        if self.panel_type_combo.currentText() == "custom":
            panel_type = self.panel_type_input.text().strip()
        else:
            panel_type = self.panel_type_combo.currentText()
            
        if panel_type:
            spec_data["panelType"] = panel_type
            keywords.append(f"intitle:{panel_type}")
            
        lineup = self.lineup_input.text().strip()
        if lineup:
            spec_data["lineup"] = lineup
            keywords.append(f"intitle:{lineup}")
            
        if self.resolution_combo.currentText() == "custom":
            resolution = self.resolution_input.text().strip()
        else:
            resolution = self.resolution_combo.currentText()
            
        if resolution:
            spec_data["resolution"] = resolution
            keywords.append(f"intitle:{resolution}")
            
        # 다중 선택 필드 수집
        sizes = []
        for checkbox in self.size_checkboxes:
            if checkbox.isChecked():
                sizes.append(checkbox.text())
                
        if self.size_custom_input.text().strip():
            sizes.append(self.size_custom_input.text().strip())
            
        if sizes:
            spec_data["size"] = sizes
            size_keywords = [f"intitle:{s}" for s in sizes]
            keywords.append(f"({' OR '.join(size_keywords)})")
            
        refresh_rates = []
        for checkbox in self.refresh_checkboxes:
            if checkbox.isChecked():
                refresh_rates.append(checkbox.text().replace("Hz", ""))
                
        if self.refresh_custom_input.text().strip():
            refresh_rates.append(self.refresh_custom_input.text().strip())
            
        if refresh_rates:
            spec_data["refreshRate"] = refresh_rates
            refresh_keywords = [f"intitle:{r}Hz" for r in refresh_rates]
            keywords.append(f"({' OR '.join(refresh_keywords)})")
            
        # 동적 필드 수집
        custom_specs = []
        for i in range(self.dynamic_specs_container.count() - 2):  # -2는 버튼과 라벨 제외
            layout = self.dynamic_specs_container.itemAt(i).layout()
            if layout:
                key_input = layout.itemAt(0).widget()
                value_input = layout.itemAt(1).widget()
                key = key_input.text().strip()
                value = value_input.text().strip()
                if key and value:
                    custom_specs.append({"key": key, "value": value})
                    keywords.append(f"{value}")
                    
        if custom_specs:
            spec_data["custom_specs"] = custom_specs
            
        # 쿼리 생성
        keyword_query = " AND ".join(keywords)
        site_list = selected_media
        
        self.add_log(f"검색 쿼리: {keyword_query}", "info")
        self.add_log(f"대상 사이트: {', '.join(site_list)}", "info")
        
        # 검색 작업 시작
        # 검색 작업을 별도의 스레드에서 실행하여 UI가 freeze되지 않도록 함
        self.search_thread = QThread()
        self.create_search_worker()
        self.search_worker.moveToThread(self.search_thread)
        self.search_thread.started.connect(
            lambda: self.search_worker.start_search.emit(keyword_query, site_list)
        )
        self.search_worker.search_finished.connect(self.search_thread.quit)
        self.search_worker.search_finished.connect(self.search_worker.deleteLater)
        self.search_thread.finished.connect(self.search_thread.deleteLater)
        self.search_thread.start()
        
    def start_export(self):
        """댓글 수집 시작"""
        # 버튼 비활성화
        self.export_button.setEnabled(False)
        self.export_button.setText("댓글 수집 중. ..")
        
        # 로그 초기화
        self.log_text.clear()
        self.status_label.setText("댓글 수집 중. ..")
        self.status_label.setStyleSheet("color: #2563eb;")
        self.download_button.hide()

        # options
        options = {
            "start_date" : self.start_date.date().toString("yyyy-MM-dd"),
            "end_date": self.end_date.date().toString("yyyy-MM-dd")
        }
        
        # 검색 결과 URL 사용
        urls = []
        for i in range(self.search_results_list_container.count()):
            widget = self.search_results_list_container.itemAt(i).widget()
            if widget:
                # 위젯 내부의 QLabel에서 URL 추출
                for j in range(widget.layout().count()):
                    item = widget.layout().itemAt(j)
                    if isinstance(item.widget(), QLabel):
                        urls.append(item.widget().text())
                        break
        self.add_log(f"댓글 수집 시작: {len(urls)}개 URL", "info")
        
        # 댓글 수집 작업 시작
        self.export_thread = QThread()
        self.create_export_worker()
        self.export_worker.moveToThread(self.export_thread)
        self.export_thread.started.connect(
            lambda: self.export_worker.start_export.emit(urls, options)
        )
        self.export_worker.export_finished.connect(self.export_thread.quit)
        self.export_worker.export_finished.connect(self.export_worker.deleteLater)
        self.export_thread.finished.connect(self.export_thread.deleteLater)
        self.export_thread.start()

    def on_search_started(self, message):
        self.add_log(message, "success")
        
    def on_search_progress(self, message):
        self.add_log(message, "info")
        
    def on_search_finished(self, results):
        self.add_log(f"검색 완료: {len(results)}개 결과", "success")
        # 검색 결과 표시
        self.clear_search_results_list()
        for url in results:
            self.add_search_result_item(url)
        # 수집 시작 버튼 표시
        self.export_button.show()
        self.export_button.setEnabled(True)
        self.export_button.setText("댓글 수집 시작")
        # 검색 완료 후 버튼 상태 초기화
        self.reset_button_state()
        
    def on_export_started(self, message):
        self.add_log(message, "warn")
        
    def on_export_progress(self, message):
        self.add_log(message, "info")
        
    def on_export_finished(self, result):
        self.add_log("댓글 수집 완료", "success")
        self.add_log(f"총 {len(result['results'])}개 데이터 수집 완료", "info")
        self.export_results = result['results']
        self.show_download_button()
        
    def on_error(self, message):
        self.add_log(message, "error")
        self.status_label.setText("오류 발생")
        self.status_label.setStyleSheet("color: #ef4444;")
        self.reset_button_state()
        
    def add_log(self, message, level="info"):
        """로그 추가"""
        time_str = datetime.now().strftime("%H:%M:%S")
        if level == "error":
            formatted_message = f"[{time_str}] ❌ {message}"
        elif level == "success":
            formatted_message = f"[{time_str}] ✅ {message}"
        elif level == "warn":
            formatted_message = f"[{time_str}] ⚠️ {message}"
        else:
            formatted_message = f"[{time_str}] {message}"
            
        self.log_text.append(formatted_message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        
    def show_download_button(self):
        """다운로드 버튼 표시"""
        self.status_label.setText("완료됨")
        self.status_label.setStyleSheet("color: #10b981;")
        self.download_button.show()
        
    def download_results(self):
        """결과 다운로드"""
        if self.export_results:
            # JSON 파일로 저장
            try:
                # 결과 데이터를 JSON으로 변환
                json_data = json.dumps(self.export_results, ensure_ascii=False, indent=2)
                
                # 파일 저장 다이얼로그 표시
                from PySide6.QtWidgets import QFileDialog
                file_path, _ = QFileDialog.getSaveFileName(
                    self, 
                    "결과 저장", 
                    "export_comments_result.json", 
                    "JSON Files (*.json)"
                )
                
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(json_data)
                    self.add_log(f"결과가 {file_path}에 저장되었습니다.", "success")
            except Exception as e:
                self.add_log(f"파일 저장 오류: {str(e)}", "error")
        else:
            self.add_log("다운로드할 데이터가 없습니다.", "error")
            
    def reset_button_state(self):
        """버튼 상태 초기화"""
        self.submit_button.setEnabled(True)
        self.submit_button.setText("URL 검색 시작하기")
        
    def add_search_url(self):
        """검색 URL 추가"""
        url = self.search_input.text().strip()
        if url:
            self.add_search_result_item(url)
            self.search_input.clear()
            
    def add_search_result_item(self, url):
        """검색 결과 항목 추가 (사용자 정의 위젯)"""
        # 항목 컨테이너 위젯 생성
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(5, 5, 5, 5)
        item_layout.setSpacing(5)
        
        # URL 라벨
        url_label = QLabel(url)
        url_label.setWordWrap(True)
        url_label.setMinimumWidth(300)
        url_label.setObjectName("SearchResultUrl")
        item_layout.addWidget(url_label)
        
        # 삭제 버튼
        remove_button = QPushButton("×")
        remove_button.setFixedSize(25, 25)
        remove_button.clicked.connect(lambda: self.remove_search_result_item(item_widget))
        item_layout.addWidget(remove_button)
        
        # 항목을 컨테이너에 추가
        self.search_results_list_container.addWidget(item_widget)
        
    def remove_search_result_item(self, item_widget):
        """검색 결과 항목 삭제"""
        self.search_results_list_container.removeWidget(item_widget)
        item_widget.deleteLater()
        
    def clear_search_results_list(self):
        """검색 결과 리스트 초기화"""
        for i in reversed(range(self.search_results_list_container.count())):
            widget = self.search_results_list_container.itemAt(i).widget()
            if widget:
                self.search_results_list_container.removeWidget(widget)
                widget.deleteLater()
                
    def show_search_result_context_menu(self, position):
        """검색 결과 리스트 컨텍스트 메뉴 표시"""
        # 기존의 컨텍스트 메뉴는 제거하고, 사용자 정의 위젯의 삭제 기능을 사용
        pass

def main():
    app = QApplication(sys.argv)
    
    # 어플리케이션 스타일 설정
    app.setStyle("Fusion")
    
    # 테마 설정
    palette = app.palette()
    palette.setColor(QPalette.Window, Qt.white)
    palette.setColor(QPalette.WindowText, Qt.black)
    palette.setColor(QPalette.Base, Qt.white)
    palette.setColor(QPalette.AlternateBase, Qt.white)
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.black)
    palette.setColor(QPalette.Text, Qt.black)
    palette.setColor(QPalette.Button, Qt.white)
    palette.setColor(QPalette.ButtonText, Qt.black)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Highlight, Qt.blue)
    palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
