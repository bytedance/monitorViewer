# Copyright (c) 2024 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: GPL-3.0-only
# -*- coding: utf-8 -*-

import os
import re
import sys
import copy
import yaml
import json
import getpass
import argparse
import datetime
import qdarkstyle

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QAction, qApp, QTabWidget, QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QMessageBox, QLineEdit, QComboBox, QHeaderView, QDateEdit, QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QDate

sys.path.append(os.environ['MONITOR_VIEWER_INSTALL_PATH'])
from common import common_monitor
from common import common_pyqt5
from config import config

os.environ['PYTHONUNBUFFERED'] = '1'
VERSION = 'V1.0'
VERSION_DATE = '2024.10.31'

# Solve some unexpected warning message.
if 'XDG_RUNTIME_DIR' not in os.environ:
    user = getpass.getuser()
    os.environ['XDG_RUNTIME_DIR'] = '/tmp/runtime-' + str(user)

    if not os.path.exists(os.environ['XDG_RUNTIME_DIR']):
        os.makedirs(os.environ['XDG_RUNTIME_DIR'])
        os.chmod(os.environ['XDG_RUNTIME_DIR'], 0o777)


def read_args():
    """
    Read in arguments.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('-t', '--tab',
                        default='MONITOR',
                        choices=['MONITOR', 'HEARTBEAT', 'LOG', 'ALARM'],
                        help='Specify current tab, default is "MONITOR" tab.')

    args = parser.parse_args()

    return args.tab


class MainWindow(QMainWindow):
    """
    Main window of monitorViewer.
    """
    def __init__(self, specified_tab):
        super().__init__()

        # Heartbeat check.
        self.heartbeat_check()

        # Get monitorViewer database information.
        self.db_dic = self.get_db_info()

        # Generate GUI.
        self.init_ui()

        # For pre-set tab.
        self.switch_tab(specified_tab)

    def heartbeat_check(self):
        """
        Check script/default/check_script_heartbeat script execute normally or not.
        """
        if hasattr(config, 'db_path') and os.path.exists(config.db_path):
            check_script_heartbeat_db_path = str(config.db_path) + '/default/check_script_heartbeat/heartbeat'
            today = datetime.datetime.now().strftime('%Y%m%d')
            today_path = str(check_script_heartbeat_db_path) + '/' + str(today)
            yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y%m%d')
            yesterday_path = str(check_script_heartbeat_db_path) + '/' + str(yesterday)

            if (not os.path.exists(today_path)) and (not os.path.exists(yesterday_path)):
                common_monitor.bprint('Heartbeat check script have been stoped abnormally for over a day.', level='Error')
                check_script_heartbeat_path = str(os.environ['MONITOR_VIEWER_INSTALL_PATH']) + '/scripts/default/check_script_heartbeat'

                if os.path.exists(check_script_heartbeat_path):
                    common_monitor.bprint('Execute heartbeat check script "' + str(check_script_heartbeat_path) + '" ...', level='Info')
                    common_monitor.run_command(check_script_heartbeat_path)
                else:
                    common_monitor.bprint('Heartbeat check script "' + str(check_script_heartbeat_path) + '" is missing, please have a check ...', level='Warning')

    def get_db_info(self):
        """
        Get monitorViewer database info from config.db_path.
        """
        db_dic = {}

        if hasattr(config, 'db_path') and os.path.exists(config.db_path):
            # Get valid_direction_dic.
            valid_direction_dic = {}

            if hasattr(config, 'valid_direction_dic') and config.valid_direction_dic:
                valid_direction_dic = config.valid_direction_dic

            # Get direction information from coinfig.db_path.
            for direction in os.listdir(config.db_path):
                if direction in valid_direction_dic.keys():
                    db_dic.setdefault(direction, {})
                    direction_path = str(config.db_path) + '/' + str(direction)

                    for monitor_item in os.listdir(direction_path):
                        monitor_item_path = str(direction_path) + '/' + str(monitor_item)
                        dir_name_list = list(os.listdir(monitor_item_path))

                        if 'monitor_item.yaml' in dir_name_list:
                            db_dic[direction].setdefault(monitor_item, {'info': {}, 'heartbeat_path': '', 'log_path': '', 'alarm_path': ''})

                        for dir_name in dir_name_list:
                            dir_path = str(monitor_item_path) + '/' + str(dir_name)

                            if (dir_name == 'monitor_item.yaml') and os.path.isfile(dir_path):
                                with open(dir_path, 'r') as DP:
                                    db_dic[direction][monitor_item]['info'] = yaml.load(DP, Loader=yaml.FullLoader)
                            elif (dir_name == 'heartbeat') and os.path.isdir(dir_path):
                                db_dic[direction][monitor_item]['heartbeat_path'] = dir_path
                            elif (dir_name == 'log') and os.path.isdir(dir_path):
                                db_dic[direction][monitor_item]['log_path'] = dir_path
                            elif (dir_name == 'alarm') and os.path.isdir(dir_path):
                                db_dic[direction][monitor_item]['alarm_path'] = dir_path

        return db_dic

    def init_ui(self):
        """
        Main process, draw the main graphic frame.
        """
        # Add menubar.
        self.gen_menubar()

        # Define top Tab widget.
        self.main_tab = QTabWidget(self)
        self.setCentralWidget(self.main_tab)

        # Define sub-tabs.
        self.monitor_tab = QWidget()
        self.heartbeat_tab = QWidget()
        self.log_tab = QWidget()
        self.alarm_tab = QWidget()

        # Add the sub-tabs into top Tab widget.
        self.main_tab.addTab(self.monitor_tab, 'MONITOR')
        self.main_tab.addTab(self.heartbeat_tab, 'HEARTBEAT')
        self.main_tab.addTab(self.log_tab, 'LOG')
        self.main_tab.addTab(self.alarm_tab, 'ALARM')

        # Generate the sub-tabs
        self.gen_monitor_tab()
        self.gen_heartbeat_tab()
        self.gen_log_tab()
        self.gen_alarm_tab()

        # Show main windows
        common_pyqt5.auto_resize(self, 1200, 565)
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.setWindowTitle('monitorViewer ' + str(VERSION))
        self.setWindowIcon(QIcon(str(os.environ['MONITOR_VIEWER_INSTALL_PATH']) + '/data/pictures/monitor.ico'))
        common_pyqt5.center_window(self)

    def gen_menubar(self):
        """
        Generate menubar.
        """
        menubar = self.menuBar()

        # File
        export_monitor_table_action = QAction('Export monitor table', self)
        export_monitor_table_action.setIcon(QIcon(str(os.environ['MONITOR_VIEWER_INSTALL_PATH']) + '/data/pictures/save.png'))
        export_monitor_table_action.triggered.connect(self.export_monitor_table)

        export_heartbeat_table_action = QAction('Export heartbeat table', self)
        export_heartbeat_table_action.setIcon(QIcon(str(os.environ['MONITOR_VIEWER_INSTALL_PATH']) + '/data/pictures/save.png'))
        export_heartbeat_table_action.triggered.connect(self.export_heartbeat_table)

        export_log_table_action = QAction('Export log table', self)
        export_log_table_action.setIcon(QIcon(str(os.environ['MONITOR_VIEWER_INSTALL_PATH']) + '/data/pictures/save.png'))
        export_log_table_action.triggered.connect(self.export_log_table)

        export_alarm_table_action = QAction('Export alarm table', self)
        export_alarm_table_action.setIcon(QIcon(str(os.environ['MONITOR_VIEWER_INSTALL_PATH']) + '/data/pictures/save.png'))
        export_alarm_table_action.triggered.connect(self.export_alarm_table)

        exit_action = QAction('Exit', self)
        exit_action.setIcon(QIcon(str(os.environ['MONITOR_VIEWER_INSTALL_PATH']) + '/data/pictures/exit.png'))
        exit_action.triggered.connect(qApp.quit)

        file_menu = menubar.addMenu('File')
        file_menu.addAction(export_monitor_table_action)
        file_menu.addAction(export_heartbeat_table_action)
        file_menu.addAction(export_log_table_action)
        file_menu.addAction(export_alarm_table_action)
        file_menu.addAction(exit_action)

        # Help
        version_action = QAction('Version', self)
        version_action.setIcon(QIcon(str(os.environ['MONITOR_VIEWER_INSTALL_PATH']) + '/data/pictures/version.png'))
        version_action.triggered.connect(self.show_version)

        about_action = QAction('About monitorViewer', self)
        about_action.setIcon(QIcon(str(os.environ['MONITOR_VIEWER_INSTALL_PATH']) + '/data/pictures/about.png'))
        about_action.triggered.connect(self.show_about)

        help_menu = menubar.addMenu('Help')
        help_menu.addAction(version_action)
        help_menu.addAction(about_action)

    def show_version(self):
        """
        Show monitorViewer version information.
        """
        QMessageBox.about(self, 'MonitorViewer', 'Version: ' + str(VERSION) + ' (' + str(VERSION_DATE) + ')')

    def show_about(self):
        """
        Show monitorViewer about information.
        """
        about_message = """
Thanks for downloading monitorViewer.

MonitorViewer includes a python framework for customing monitoring scripts and a set of information
dashboards. Users can easily customize their monitoring items based on monitorViewer.

Please be free to contact liyanqing1987@163.com if any question."""
        QMessageBox.about(self, 'monitorViewer About', about_message)

# For MONITOR TAB (start) #
    def gen_monitor_tab(self):
        """
        Generate MONITOR tab, show monitor item information.
        """
        self.monitor_tab_table = QTableWidget(self.monitor_tab)

        # Grid
        monitor_tab_grid = QGridLayout()
        monitor_tab_grid.addWidget(self.monitor_tab_table, 0, 0)
        self.monitor_tab.setLayout(monitor_tab_grid)

        # Generate self.monitor_tab_table
        self.gen_monitor_tab_table()

    def gen_monitor_tab_table(self):
        """
        Generate self.monitor_tab_table.
        """
        self.monitor_tab_table.setShowGrid(True)
        self.monitor_tab_table.setSortingEnabled(True)
        self.monitor_tab_table.setColumnCount(0)
        self.monitor_tab_table_title_list = ['Direction', 'Admin', 'Item', 'Startup', 'Host', 'Exec_Frequency', 'Alarm_Frequency', 'Script']
        self.monitor_tab_table.setColumnCount(len(self.monitor_tab_table_title_list))
        self.monitor_tab_table.setHorizontalHeaderLabels(self.monitor_tab_table_title_list)

        # Set column width
        self.monitor_tab_table.setColumnWidth(0, 80)
        self.monitor_tab_table.setColumnWidth(1, 120)
        self.monitor_tab_table.setColumnWidth(2, 180)
        self.monitor_tab_table.setColumnWidth(3, 80)
        self.monitor_tab_table.setColumnWidth(4, 120)
        self.monitor_tab_table.setColumnWidth(5, 130)
        self.monitor_tab_table.setColumnWidth(6, 130)
        self.monitor_tab_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)

        # Set self.monitor_tab_table.setRowCount
        row = 0

        for direction in self.db_dic.keys():
            for monitor_item in self.db_dic[direction].keys():
                row += 1

        self.monitor_tab_table.setRowCount(row)

        # Set item
        row = -1

        for direction in self.db_dic.keys():
            for monitor_item in self.db_dic[direction].keys():
                column = 0
                row += 1

                # For "Direction"
                item = QTableWidgetItem()
                item.setText(direction)
                self.monitor_tab_table.setItem(row, column, item)

                # For "Admin"
                column += 1
                item = QTableWidgetItem()

                if 'direction_admin' in self.db_dic[direction][monitor_item]['info'].keys():
                    item.setText(self.db_dic[direction][monitor_item]['info']['direction_admin'])

                self.monitor_tab_table.setItem(row, column, item)

                # For "Item"
                column += 1
                item = QTableWidgetItem()
                item.setText(monitor_item)
                self.monitor_tab_table.setItem(row, column, item)

                # For "Startup"
                column += 1
                item = QTableWidgetItem()

                if 'script_startup_method' in self.db_dic[direction][monitor_item]['info'].keys():
                    item.setText(self.db_dic[direction][monitor_item]['info']['script_startup_method'])

                self.monitor_tab_table.setItem(row, column, item)

                # For "Host"
                column += 1
                item = QTableWidgetItem()

                if 'script_startup_host' in self.db_dic[direction][monitor_item]['info'].keys():
                    item.setText(self.db_dic[direction][monitor_item]['info']['script_startup_host'])

                self.monitor_tab_table.setItem(row, column, item)

                # For "Frequency"
                column += 1
                item = QTableWidgetItem()

                if 'script_execute_frequency' in self.db_dic[direction][monitor_item]['info'].keys():
                    item.setText(self.db_dic[direction][monitor_item]['info']['script_execute_frequency'])

                self.monitor_tab_table.setItem(row, column, item)

                # For "Alarm_Frequency"
                column += 1
                item = QTableWidgetItem()

                if 'alarm_frequency' in self.db_dic[direction][monitor_item]['info'].keys():
                    item.setText(self.db_dic[direction][monitor_item]['info']['alarm_frequency'])

                self.monitor_tab_table.setItem(row, column, item)

                # For "Script"
                column += 1
                item = QTableWidgetItem()

                if 'script_path' in self.db_dic[direction][monitor_item]['info'].keys():
                    item.setText(self.db_dic[direction][monitor_item]['info']['script_path'])

                self.monitor_tab_table.setItem(row, column, item)
# For MONITOR TAB (end) #

# For HEARTBEAT TAB (start) #
    def gen_heartbeat_tab(self):
        """
        Generate HEARTBEAT tab, show monitor item heartbeat information.
        """
        self.heartbeat_tab_frame = QFrame(self.heartbeat_tab)
        self.heartbeat_tab_frame.setFrameShadow(QFrame.Raised)
        self.heartbeat_tab_frame.setFrameShape(QFrame.Box)

        self.heartbeat_tab_table = QTableWidget(self.heartbeat_tab)
        self.heartbeat_tab_table.setContextMenuPolicy(Qt.CustomContextMenu)

        # Grid
        heartbeat_tab_grid = QGridLayout()

        heartbeat_tab_grid.addWidget(self.heartbeat_tab_frame, 0, 0)
        heartbeat_tab_grid.addWidget(self.heartbeat_tab_table, 1, 0)

        heartbeat_tab_grid.setRowStretch(0, 1)
        heartbeat_tab_grid.setRowStretch(1, 10)

        self.heartbeat_tab.setLayout(heartbeat_tab_grid)

        # Generate self.heartbeat_tab_frame and self.heartbeat_tab_table
        self.gen_heartbeat_tab_frame()
        self.gen_heartbeat_tab_table()

    def gen_heartbeat_tab_frame(self):
        """
        Generate (initialize) self.heartbeat_tab_frame.
        """
        # Begin_Date
        heartbeat_tab_begin_date_label = QLabel('Begin_Date', self.heartbeat_tab_frame)
        heartbeat_tab_begin_date_label.setStyleSheet("font-weight: bold;")
        heartbeat_tab_begin_date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.heartbeat_tab_begin_date_edit = QDateEdit(self.heartbeat_tab_frame)
        self.heartbeat_tab_begin_date_edit.setDisplayFormat('yyyy-MM-dd')
        self.heartbeat_tab_begin_date_edit.setMinimumDate(QDate.currentDate().addDays(-3652))
        self.heartbeat_tab_begin_date_edit.setCalendarPopup(True)
        self.heartbeat_tab_begin_date_edit.setDate(QDate.currentDate().addDays(-7))

        # End_Date
        heartbeat_tab_end_date_label = QLabel('End_Date', self.heartbeat_tab_frame)
        heartbeat_tab_end_date_label.setStyleSheet("font-weight: bold;")
        heartbeat_tab_end_date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.heartbeat_tab_end_date_edit = QDateEdit(self.heartbeat_tab_frame)
        self.heartbeat_tab_end_date_edit.setDisplayFormat('yyyy-MM-dd')
        self.heartbeat_tab_end_date_edit.setMinimumDate(QDate.currentDate().addDays(-3652))
        self.heartbeat_tab_end_date_edit.setCalendarPopup(True)
        self.heartbeat_tab_end_date_edit.setDate(QDate.currentDate())

        # Direction
        heartbeat_tab_direction_label = QLabel('Direction', self.heartbeat_tab_frame)
        heartbeat_tab_direction_label.setStyleSheet('font-weight: bold;')
        heartbeat_tab_direction_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.heartbeat_tab_direction_combo = QComboBox(self.heartbeat_tab_frame)
        self.set_heartbeat_tab_direction_combo()
        self.heartbeat_tab_direction_combo.activated.connect(self.set_heartbeat_tab_monitor_item_combo)

        # Monitor_Item
        heartbeat_tab_monitor_item_label = QLabel('Monitor_Item', self.heartbeat_tab_frame)
        heartbeat_tab_monitor_item_label.setStyleSheet('font-weight: bold;')
        heartbeat_tab_monitor_item_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.heartbeat_tab_monitor_item_combo = QComboBox(self.heartbeat_tab_frame)
        self.set_heartbeat_tab_monitor_item_combo()

        # Check button
        heartbeat_tab_check_button = QPushButton('Check', self.heartbeat_tab_frame)
        heartbeat_tab_check_button.setStyleSheet('''QPushButton:hover{background:rgb(170, 255, 127);}''')
        heartbeat_tab_check_button.clicked.connect(self.filter_heartbeat_tab)

        # self.heartbeat_tab_frame - Grid
        heartbeat_tab_frame_grid = QGridLayout()

        heartbeat_tab_frame_grid.addWidget(heartbeat_tab_begin_date_label, 0, 0)
        heartbeat_tab_frame_grid.addWidget(self.heartbeat_tab_begin_date_edit, 0, 1)
        heartbeat_tab_frame_grid.addWidget(heartbeat_tab_end_date_label, 0, 2)
        heartbeat_tab_frame_grid.addWidget(self.heartbeat_tab_end_date_edit, 0, 3)
        heartbeat_tab_frame_grid.addWidget(heartbeat_tab_direction_label, 0, 4)
        heartbeat_tab_frame_grid.addWidget(self.heartbeat_tab_direction_combo, 0, 5)
        heartbeat_tab_frame_grid.addWidget(heartbeat_tab_monitor_item_label, 0, 6)
        heartbeat_tab_frame_grid.addWidget(self.heartbeat_tab_monitor_item_combo, 0, 7)
        heartbeat_tab_frame_grid.addWidget(heartbeat_tab_check_button, 0, 8)

        heartbeat_tab_frame_grid.setColumnStretch(0, 1)
        heartbeat_tab_frame_grid.setColumnStretch(1, 1)
        heartbeat_tab_frame_grid.setColumnStretch(2, 1)
        heartbeat_tab_frame_grid.setColumnStretch(3, 1)
        heartbeat_tab_frame_grid.setColumnStretch(4, 1)
        heartbeat_tab_frame_grid.setColumnStretch(5, 1)
        heartbeat_tab_frame_grid.setColumnStretch(6, 1)
        heartbeat_tab_frame_grid.setColumnStretch(7, 1)
        heartbeat_tab_frame_grid.setColumnStretch(8, 1)

        self.heartbeat_tab_frame.setLayout(heartbeat_tab_frame_grid)

    def set_heartbeat_tab_direction_combo(self):
        """
        Set (initialize) self.heartbeat_tab_direction_combo.
        """
        self.heartbeat_tab_direction_combo.clear()

        for direction in self.db_dic.keys():
            self.heartbeat_tab_direction_combo.addItem(direction)

    def set_heartbeat_tab_monitor_item_combo(self):
        """
        Set (initialize) self.heartbeat_tab_monitor_item_combo.
        """
        self.heartbeat_tab_monitor_item_combo.clear()
        current_direction = self.heartbeat_tab_direction_combo.currentText().strip()

        if current_direction:
            for monitor_item in self.db_dic[current_direction].keys():
                self.heartbeat_tab_monitor_item_combo.addItem(monitor_item)

    def filter_heartbeat_tab(self):
        """
        Update self.heartbeat_tab_table with self.heartbeat_tab_frame settings.
        """
        begin_date = self.heartbeat_tab_begin_date_edit.text()
        begin_date = int(re.sub(r'-', '', begin_date))
        end_date = self.heartbeat_tab_end_date_edit.text()
        end_date = int(re.sub(r'-', '', end_date))
        current_direction = self.heartbeat_tab_direction_combo.currentText().strip()
        current_monitor_item = self.heartbeat_tab_monitor_item_combo.currentText().strip()
        heartbeat_info_list = self.get_heartbeat_db_info(begin_date, end_date, current_direction, current_monitor_item)

        self.gen_heartbeat_tab_table(heartbeat_info_list)

    def get_heartbeat_db_info(self, begin_date, end_date, direction, monitor_item):
        """
        Get heartbeat information with specified direction/monitor_item/begin_date/end_date information.
        """
        heartbeat_info_list = []

        if begin_date and end_date and direction and monitor_item and self.db_dic[direction][monitor_item]['heartbeat_path'] and os.path.exists(self.db_dic[direction][monitor_item]['heartbeat_path']):
            for date_file_name in os.listdir(self.db_dic[direction][monitor_item]['heartbeat_path']):
                if re.match(r'^\d{8}$', date_file_name) and (begin_date <= int(date_file_name) <= end_date):
                    date_file = str(self.db_dic[direction][monitor_item]['heartbeat_path']) + '/' + str(date_file_name)

                    with open(date_file, 'r') as DF:
                        for line in DF.readlines():
                            heartbeat_info_dic = json.loads(line.strip())
                            heartbeat_info_list.append(heartbeat_info_dic)

        return heartbeat_info_list

    def gen_heartbeat_tab_table(self, heartbeat_info_list=[]):
        """
        Generate self.heartbeat_tab_table.
        """
        self.heartbeat_tab_table.setShowGrid(True)
        self.heartbeat_tab_table.setSortingEnabled(True)
        self.heartbeat_tab_table.setRowCount(0)
        self.heartbeat_tab_table.setColumnCount(0)
        self.heartbeat_tab_table_title_list = ['Time', 'User', 'Host', 'Script']
        self.heartbeat_tab_table.setColumnCount(len(self.heartbeat_tab_table_title_list))
        self.heartbeat_tab_table.setHorizontalHeaderLabels(self.heartbeat_tab_table_title_list)

        # Set column width
        self.heartbeat_tab_table.setColumnWidth(0, 160)
        self.heartbeat_tab_table.setColumnWidth(1, 120)
        self.heartbeat_tab_table.setColumnWidth(2, 120)
        self.heartbeat_tab_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        if not heartbeat_info_list:
            return

        # Set self.heartbeat_tab_table.setRowCount
        self.heartbeat_tab_table.setRowCount(len(heartbeat_info_list))

        # Set item
        row = -1

        for heartbeat_dic in heartbeat_info_list:
            row += 1

            # For Time
            column = 0
            item = QTableWidgetItem()
            item.setText(heartbeat_dic['time'])
            self.heartbeat_tab_table.setItem(row, column, item)

            # For User
            column = 1
            item = QTableWidgetItem()
            item.setText(heartbeat_dic['user'])
            self.heartbeat_tab_table.setItem(row, column, item)

            # For Host
            column = 2
            item = QTableWidgetItem()
            item.setText(heartbeat_dic['host'])
            self.heartbeat_tab_table.setItem(row, column, item)

            # For Script
            column = 3
            item = QTableWidgetItem()
            item.setText(heartbeat_dic['script'])
            self.heartbeat_tab_table.setItem(row, column, item)
# For HEARTBEAT TAB (end) #

# For LOG TAB (start) #
    def gen_log_tab(self):
        """
        Generate LOG tab, show monitor item log information.
        """
        self.log_tab_frame = QFrame(self.log_tab)
        self.log_tab_frame.setFrameShadow(QFrame.Raised)
        self.log_tab_frame.setFrameShape(QFrame.Box)

        self.log_tab_table = QTableWidget(self.log_tab)
        self.log_tab_table.setContextMenuPolicy(Qt.CustomContextMenu)

        # Grid
        log_tab_grid = QGridLayout()

        log_tab_grid.addWidget(self.log_tab_frame, 0, 0)
        log_tab_grid.addWidget(self.log_tab_table, 1, 0)

        log_tab_grid.setRowStretch(0, 1)
        log_tab_grid.setRowStretch(1, 10)

        self.log_tab.setLayout(log_tab_grid)

        # Generate self.log_tab_frame and self.log_tab_table
        self.gen_log_tab_frame()
        self.gen_log_tab_table()

    def gen_log_tab_frame(self):
        """
        Generate (initialize) self.log_tab_frame.
        """
        # Begin_Date
        log_tab_begin_date_label = QLabel('Begin_Date', self.log_tab_frame)
        log_tab_begin_date_label.setStyleSheet("font-weight: bold;")
        log_tab_begin_date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.log_tab_begin_date_edit = QDateEdit(self.log_tab_frame)
        self.log_tab_begin_date_edit.setDisplayFormat('yyyy-MM-dd')
        self.log_tab_begin_date_edit.setMinimumDate(QDate.currentDate().addDays(-3652))
        self.log_tab_begin_date_edit.setCalendarPopup(True)
        self.log_tab_begin_date_edit.setDate(QDate.currentDate().addDays(-7))

        # End_Date
        log_tab_end_date_label = QLabel('End_Date', self.log_tab_frame)
        log_tab_end_date_label.setStyleSheet("font-weight: bold;")
        log_tab_end_date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.log_tab_end_date_edit = QDateEdit(self.log_tab_frame)
        self.log_tab_end_date_edit.setDisplayFormat('yyyy-MM-dd')
        self.log_tab_end_date_edit.setMinimumDate(QDate.currentDate().addDays(-3652))
        self.log_tab_end_date_edit.setCalendarPopup(True)
        self.log_tab_end_date_edit.setDate(QDate.currentDate())

        # Direction
        log_tab_direction_label = QLabel('Direction', self.log_tab_frame)
        log_tab_direction_label.setStyleSheet('font-weight: bold;')
        log_tab_direction_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.log_tab_direction_combo = QComboBox(self.log_tab_frame)
        self.set_log_tab_direction_combo()
        self.log_tab_direction_combo.activated.connect(self.set_log_tab_monitor_item_combo)

        # Monitor_Item
        log_tab_monitor_item_label = QLabel('Monitor_Item', self.log_tab_frame)
        log_tab_monitor_item_label.setStyleSheet('font-weight: bold;')
        log_tab_monitor_item_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.log_tab_monitor_item_combo = QComboBox(self.log_tab_frame)
        self.set_log_tab_monitor_item_combo()

        # Message_Level
        log_tab_message_level_label = QLabel('Message_Level', self.log_tab_frame)
        log_tab_message_level_label.setStyleSheet('font-weight: bold;')
        log_tab_message_level_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.log_tab_message_level_combo = QComboBox(self.log_tab_frame)
        self.set_log_tab_message_level_combo()

        # Keyword
        log_tab_keyword_label = QLabel('Keyword', self.log_tab_frame)
        log_tab_keyword_label.setStyleSheet('font-weight: bold;')
        log_tab_keyword_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.log_tab_keyword_line = QLineEdit()

        # Check button
        log_tab_check_button = QPushButton('Check', self.log_tab_frame)
        log_tab_check_button.setStyleSheet('''QPushButton:hover{background:rgb(170, 255, 127);}''')
        log_tab_check_button.clicked.connect(self.filter_log_tab)

        # self.log_tab_frame - Grid
        log_tab_frame_grid = QGridLayout()

        log_tab_frame_grid.addWidget(log_tab_begin_date_label, 0, 0)
        log_tab_frame_grid.addWidget(self.log_tab_begin_date_edit, 0, 1)
        log_tab_frame_grid.addWidget(log_tab_end_date_label, 0, 2)
        log_tab_frame_grid.addWidget(self.log_tab_end_date_edit, 0, 3)
        log_tab_frame_grid.addWidget(log_tab_direction_label, 0, 4)
        log_tab_frame_grid.addWidget(self.log_tab_direction_combo, 0, 5)
        log_tab_frame_grid.addWidget(log_tab_monitor_item_label, 0, 6)
        log_tab_frame_grid.addWidget(self.log_tab_monitor_item_combo, 0, 7)
        log_tab_frame_grid.addWidget(log_tab_message_level_label, 1, 0)
        log_tab_frame_grid.addWidget(self.log_tab_message_level_combo, 1, 1)
        log_tab_frame_grid.addWidget(log_tab_keyword_label, 1, 2)
        log_tab_frame_grid.addWidget(self.log_tab_keyword_line, 1, 3, 1, 5)
        log_tab_frame_grid.addWidget(log_tab_check_button, 1, 8)

        log_tab_frame_grid.setColumnStretch(0, 1)
        log_tab_frame_grid.setColumnStretch(1, 1)
        log_tab_frame_grid.setColumnStretch(2, 1)
        log_tab_frame_grid.setColumnStretch(3, 1)
        log_tab_frame_grid.setColumnStretch(4, 1)
        log_tab_frame_grid.setColumnStretch(5, 1)
        log_tab_frame_grid.setColumnStretch(6, 1)
        log_tab_frame_grid.setColumnStretch(7, 1)
        log_tab_frame_grid.setColumnStretch(8, 1)

        self.log_tab_frame.setLayout(log_tab_frame_grid)

    def set_log_tab_direction_combo(self):
        """
        Set (initialize) self.log_tab_direction_combo.
        """
        self.log_tab_direction_combo.clear()

        for direction in self.db_dic.keys():
            self.log_tab_direction_combo.addItem(direction)

    def set_log_tab_monitor_item_combo(self):
        """
        Set (initialize) self.log_tab_monitor_item_combo.
        """
        self.log_tab_monitor_item_combo.clear()
        current_direction = self.log_tab_direction_combo.currentText().strip()

        if current_direction:
            for monitor_item in self.db_dic[current_direction].keys():
                self.log_tab_monitor_item_combo.addItem(monitor_item)

    def set_log_tab_message_level_combo(self):
        """
        Set (initialize) self.log_tab_message_level_combo.
        """
        self.log_tab_message_level_combo.clear()
        self.log_tab_message_level_combo.addItem('')

        if hasattr(config, 'valid_message_level_list') and config.valid_message_level_list:
            for message_level in config.valid_message_level_list:
                self.log_tab_message_level_combo.addItem(message_level)

    def filter_log_tab(self):
        """
        Update self.log_tab_table with self.log_tab_frame settings.
        """
        begin_date = self.log_tab_begin_date_edit.text()
        begin_date = int(re.sub(r'-', '', begin_date))
        end_date = self.log_tab_end_date_edit.text()
        end_date = int(re.sub(r'-', '', end_date))
        current_direction = self.log_tab_direction_combo.currentText().strip()
        current_monitor_item = self.log_tab_monitor_item_combo.currentText().strip()
        current_message_level = self.log_tab_message_level_combo.currentText().strip()
        current_keyword = self.log_tab_keyword_line.text().strip()
        log_info_list = self.get_log_db_info(begin_date, end_date, current_direction, current_monitor_item, current_message_level, current_keyword)

        self.gen_log_tab_table(log_info_list)

    def get_log_db_info(self, begin_date, end_date, direction, monitor_item, specified_message_level, specified_keyword):
        """
        Get log information with specified direction/monitor_item/message_level/keyword/begin_date/end_date information.
        """
        log_info_list = []

        if begin_date and end_date and direction and monitor_item and self.db_dic[direction][monitor_item]['log_path'] and os.path.exists(self.db_dic[direction][monitor_item]['log_path']):
            for date_file_name in os.listdir(self.db_dic[direction][monitor_item]['log_path']):
                if re.match(r'^\d{8}$', date_file_name) and (begin_date <= int(date_file_name) <= end_date):
                    date_file = str(self.db_dic[direction][monitor_item]['log_path']) + '/' + str(date_file_name)

                    with open(date_file, 'r') as DF:
                        for line in DF.readlines():
                            log_info_dic = json.loads(line.strip())
                            log_info_dic['message'] = log_info_dic['message'].strip().split('\n')
                            log_info_list.append(log_info_dic)

                    # Check specified_keyword.
                    if specified_keyword and log_info_list:
                        old_log_info_list = copy.deepcopy(log_info_list)
                        log_info_list = []

                        for log_info_dic in old_log_info_list:
                            for message in log_info_dic['message']:
                                if re.search(re.escape(specified_keyword), message):
                                    log_info_list.append(log_info_dic)
                                    break

        return log_info_list

    def gen_log_tab_table(self, log_info_list=[]):
        """
        Generate self.log_tab_table.
        """
        self.log_tab_table.setShowGrid(True)
        self.log_tab_table.setSortingEnabled(True)
        self.log_tab_table.setRowCount(0)
        self.log_tab_table.setColumnCount(0)
        self.log_tab_table_title_list = ['Time', 'Message_Level', 'Message']
        self.log_tab_table.setColumnCount(len(self.log_tab_table_title_list))
        self.log_tab_table.setHorizontalHeaderLabels(self.log_tab_table_title_list)

        # Set column width
        self.log_tab_table.setColumnWidth(0, 160)
        self.log_tab_table.setColumnWidth(1, 120)
        self.log_tab_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        if not log_info_list:
            return

        # Set self.log_tab_table.setRowCount
        row = 0

        for log_dic in log_info_list:
            row += len(log_dic['message'])

        self.log_tab_table.setRowCount(row)

        # Set item
        row = -1

        for log_dic in log_info_list:
            row += 1

            # For Time
            column = 0
            item = QTableWidgetItem()
            item.setText(log_dic['time'])
            self.log_tab_table.setItem(row, column, item)

            # For Message_Level
            column = 1
            item = QTableWidgetItem()
            item.setText(log_dic['message_level'])
            self.log_tab_table.setItem(row, column, item)

            # For Message
            column = 2

            for (i, message) in enumerate(log_dic['message']):
                if i >= 1:
                    row += 1

                item = QTableWidgetItem()
                item.setText(message)
                self.log_tab_table.setItem(row, column, item)
# For LOG TAB (end) #

# For ALARM TAB (start) #
    def gen_alarm_tab(self):
        """
        Generate ALARM tab, show monitor item alarm log information.
        """
        self.alarm_tab_frame = QFrame(self.alarm_tab)
        self.alarm_tab_frame.setFrameShadow(QFrame.Raised)
        self.alarm_tab_frame.setFrameShape(QFrame.Box)

        self.alarm_tab_table = QTableWidget(self.alarm_tab)
        self.alarm_tab_table.setContextMenuPolicy(Qt.CustomContextMenu)

        # Grid
        alarm_tab_grid = QGridLayout()

        alarm_tab_grid.addWidget(self.alarm_tab_frame, 0, 0)
        alarm_tab_grid.addWidget(self.alarm_tab_table, 1, 0)

        alarm_tab_grid.setRowStretch(0, 1)
        alarm_tab_grid.setRowStretch(1, 10)

        self.alarm_tab.setLayout(alarm_tab_grid)

        # Generate self.alarm_tab_frame and self.alarm_tab_table
        self.gen_alarm_tab_frame()
        self.gen_alarm_tab_table()

    def gen_alarm_tab_frame(self):
        """
        Generate (initialize) self.alarm_tab_frame.
        """
        # Begin_Date
        alarm_tab_begin_date_label = QLabel('Begin_Date', self.alarm_tab_frame)
        alarm_tab_begin_date_label.setStyleSheet("font-weight: bold;")
        alarm_tab_begin_date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.alarm_tab_begin_date_edit = QDateEdit(self.alarm_tab_frame)
        self.alarm_tab_begin_date_edit.setDisplayFormat('yyyy-MM-dd')
        self.alarm_tab_begin_date_edit.setMinimumDate(QDate.currentDate().addDays(-3652))
        self.alarm_tab_begin_date_edit.setCalendarPopup(True)
        self.alarm_tab_begin_date_edit.setDate(QDate.currentDate().addDays(-7))

        # End_Date
        alarm_tab_end_date_label = QLabel('End_Date', self.alarm_tab_frame)
        alarm_tab_end_date_label.setStyleSheet("font-weight: bold;")
        alarm_tab_end_date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.alarm_tab_end_date_edit = QDateEdit(self.alarm_tab_frame)
        self.alarm_tab_end_date_edit.setDisplayFormat('yyyy-MM-dd')
        self.alarm_tab_end_date_edit.setMinimumDate(QDate.currentDate().addDays(-3652))
        self.alarm_tab_end_date_edit.setCalendarPopup(True)
        self.alarm_tab_end_date_edit.setDate(QDate.currentDate())

        # Direction
        alarm_tab_direction_label = QLabel('Direction', self.alarm_tab_frame)
        alarm_tab_direction_label.setStyleSheet('font-weight: bold;')
        alarm_tab_direction_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.alarm_tab_direction_combo = QComboBox(self.alarm_tab_frame)
        self.set_alarm_tab_direction_combo()
        self.alarm_tab_direction_combo.activated.connect(self.set_alarm_tab_monitor_item_combo)

        # Monitor_Item
        alarm_tab_monitor_item_label = QLabel('Monitor_Item', self.alarm_tab_frame)
        alarm_tab_monitor_item_label.setStyleSheet('font-weight: bold;')
        alarm_tab_monitor_item_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.alarm_tab_monitor_item_combo = QComboBox(self.alarm_tab_frame)
        self.set_alarm_tab_monitor_item_combo()

        # Receivers
        alarm_tab_receivers_label = QLabel('Receivers', self.alarm_tab_frame)
        alarm_tab_receivers_label.setStyleSheet('font-weight: bold;')
        alarm_tab_receivers_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.alarm_tab_receivers_line = QLineEdit()

        # Keyword
        alarm_tab_keyword_label = QLabel('Keyword', self.alarm_tab_frame)
        alarm_tab_keyword_label.setStyleSheet('font-weight: bold;')
        alarm_tab_keyword_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.alarm_tab_keyword_line = QLineEdit()

        # Check button
        alarm_tab_check_button = QPushButton('Check', self.alarm_tab_frame)
        alarm_tab_check_button.setStyleSheet('''QPushButton:hover{background:rgb(170, 255, 127);}''')
        alarm_tab_check_button.clicked.connect(self.filter_alarm_tab)

        # self.alarm_tab_frame - Grid
        alarm_tab_frame_grid = QGridLayout()

        alarm_tab_frame_grid.addWidget(alarm_tab_begin_date_label, 0, 0)
        alarm_tab_frame_grid.addWidget(self.alarm_tab_begin_date_edit, 0, 1)
        alarm_tab_frame_grid.addWidget(alarm_tab_end_date_label, 0, 2)
        alarm_tab_frame_grid.addWidget(self.alarm_tab_end_date_edit, 0, 3)
        alarm_tab_frame_grid.addWidget(alarm_tab_direction_label, 0, 4)
        alarm_tab_frame_grid.addWidget(self.alarm_tab_direction_combo, 0, 5)
        alarm_tab_frame_grid.addWidget(alarm_tab_monitor_item_label, 0, 6)
        alarm_tab_frame_grid.addWidget(self.alarm_tab_monitor_item_combo, 0, 7)
        alarm_tab_frame_grid.addWidget(alarm_tab_receivers_label, 1, 0)
        alarm_tab_frame_grid.addWidget(self.alarm_tab_receivers_line, 1, 1, 1, 3)
        alarm_tab_frame_grid.addWidget(alarm_tab_keyword_label, 1, 4)
        alarm_tab_frame_grid.addWidget(self.alarm_tab_keyword_line, 1, 5, 1, 3)
        alarm_tab_frame_grid.addWidget(alarm_tab_check_button, 1, 8)

        alarm_tab_frame_grid.setColumnStretch(0, 1)
        alarm_tab_frame_grid.setColumnStretch(1, 1)
        alarm_tab_frame_grid.setColumnStretch(2, 1)
        alarm_tab_frame_grid.setColumnStretch(3, 1)
        alarm_tab_frame_grid.setColumnStretch(4, 1)
        alarm_tab_frame_grid.setColumnStretch(5, 1)
        alarm_tab_frame_grid.setColumnStretch(6, 1)
        alarm_tab_frame_grid.setColumnStretch(7, 1)
        alarm_tab_frame_grid.setColumnStretch(8, 1)

        self.alarm_tab_frame.setLayout(alarm_tab_frame_grid)

    def set_alarm_tab_direction_combo(self):
        """
        Set (initialize) self.alarm_tab_direction_combo.
        """
        self.alarm_tab_direction_combo.clear()

        for direction in self.db_dic.keys():
            self.alarm_tab_direction_combo.addItem(direction)

    def set_alarm_tab_monitor_item_combo(self):
        """
        Set (initialize) self.alarm_tab_monitor_item_combo.
        """
        self.alarm_tab_monitor_item_combo.clear()
        current_direction = self.alarm_tab_direction_combo.currentText().strip()

        if current_direction:
            for monitor_item in self.db_dic[current_direction].keys():
                self.alarm_tab_monitor_item_combo.addItem(monitor_item)

    def filter_alarm_tab(self):
        """
        Update self.alarm_tab_table with self.alarm_tab_frame settings.
        """
        begin_date = self.alarm_tab_begin_date_edit.text()
        begin_date = int(re.sub(r'-', '', begin_date))
        end_date = self.alarm_tab_end_date_edit.text()
        end_date = int(re.sub(r'-', '', end_date))
        current_direction = self.alarm_tab_direction_combo.currentText().strip()
        current_monitor_item = self.alarm_tab_monitor_item_combo.currentText().strip()
        current_receiver_list = self.alarm_tab_receivers_line.text().strip().split()
        current_keyword = self.alarm_tab_keyword_line.text().strip()
        alarm_info_list = self.get_alarm_db_info(begin_date, end_date, current_direction, current_monitor_item, current_receiver_list, current_keyword)

        self.gen_alarm_tab_table(alarm_info_list)

    def get_alarm_db_info(self, begin_date, end_date, direction, monitor_item, specified_receiver_list, specified_keyword):
        """
        Get alarm information with specified direction/monitor_item/receivers/keyword/begin_date/end_date information.
        """
        alarm_info_list = []

        if begin_date and end_date and direction and monitor_item and self.db_dic[direction][monitor_item]['alarm_path'] and os.path.exists(self.db_dic[direction][monitor_item]['alarm_path']):
            for date_file_name in os.listdir(self.db_dic[direction][monitor_item]['alarm_path']):
                if re.match(r'^\d{8}$', date_file_name) and (begin_date <= int(date_file_name) <= end_date):
                    date_file = str(self.db_dic[direction][monitor_item]['alarm_path']) + '/' + str(date_file_name)

                    with open(date_file, 'r') as DF:
                        for line in DF.readlines():
                            alarm_info_dic = json.loads(line.strip())
                            alarm_info_dic['message'] = alarm_info_dic['message'].strip().split('\n')
                            alarm_info_list.append(alarm_info_dic)

                    # Check specified_keyword.
                    if specified_keyword and alarm_info_list:
                        old_alarm_info_list = copy.deepcopy(alarm_info_list)
                        alarm_info_list = []

                        for alarm_info_dic in old_alarm_info_list:
                            for message in alarm_info_dic['message']:
                                if re.search(re.escape(specified_keyword), message):
                                    alarm_info_list.append(alarm_info_dic)
                                    break

        return alarm_info_list

    def gen_alarm_tab_table(self, alarm_info_list=[]):
        """
        Generate self.alarm_tab_table.
        """
        self.alarm_tab_table.setShowGrid(True)
        self.alarm_tab_table.setSortingEnabled(True)
        self.alarm_tab_table.setRowCount(0)
        self.alarm_tab_table.setColumnCount(0)
        self.alarm_tab_table_title_list = ['Time', 'Receivers', 'Alarm_Result', 'Message']
        self.alarm_tab_table.setColumnCount(len(self.alarm_tab_table_title_list))
        self.alarm_tab_table.setHorizontalHeaderLabels(self.alarm_tab_table_title_list)

        # Set column width
        self.alarm_tab_table.setColumnWidth(0, 160)
        self.alarm_tab_table.setColumnWidth(1, 120)
        self.alarm_tab_table.setColumnWidth(2, 120)
        self.alarm_tab_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        if not alarm_info_list:
            return

        # Set self.alarm_tab_table.setRowCount
        row = 0

        for alarm_dic in alarm_info_list:
            row += len(alarm_dic['message'])

        self.alarm_tab_table.setRowCount(row)

        # Set item
        row = -1

        for alarm_dic in alarm_info_list:
            row += 1

            # For Time
            column = 0
            item = QTableWidgetItem()
            item.setText(alarm_dic['time'])
            self.alarm_tab_table.setItem(row, column, item)

            # For Receivers
            column = 1
            item = QTableWidgetItem()
            item.setText(alarm_dic['receivers'])
            self.alarm_tab_table.setItem(row, column, item)

            # For Alarm_Result
            column = 2
            item = QTableWidgetItem()
            item.setText(alarm_dic['send_alarm_result'])
            self.alarm_tab_table.setItem(row, column, item)

            # For Message
            column = 3

            for (i, message) in enumerate(alarm_dic['message']):
                if i >= 1:
                    row += 1

                item = QTableWidgetItem()
                item.setText(message)
                self.alarm_tab_table.setItem(row, column, item)
# For ALARM TAB (end) #

# Export table (start) #
    def export_monitor_table(self):
        self.export_table('monitor', self.monitor_tab_table, self.monitor_tab_table_title_list)

    def export_heartbeat_table(self):
        self.export_table('heartbeat', self.heartbeat_tab_table, self.heartbeat_tab_table_title_list)

    def export_log_table(self):
        self.export_table('log', self.log_tab_table, self.log_tab_table_title_list)

    def export_alarm_table(self):
        self.export_table('alarm', self.alarm_tab_table, self.alarm_tab_table_title_list)

    def export_table(self, table_type, table_item, title_list):
        """
        Export specified table info into an Excel.
        """
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_time_string = re.sub('-', '', current_time)
        current_time_string = re.sub(':', '', current_time_string)
        current_time_string = re.sub(' ', '_', current_time_string)
        default_output_file = './monitor_' + str(table_type) + '_' + str(current_time_string) + '.csv'
        (output_file, output_file_type) = QFileDialog.getSaveFileName(self, 'Export ' + str(table_type) + ' table', default_output_file, 'CSV Files (*.csv)')

        if output_file:
            # Get table content.
            content_dic = {}
            row_num = table_item.rowCount()
            column_num = table_item.columnCount()

            for column in range(column_num):
                column_list = []

                for row in range(row_num):
                    if table_item.item(row, column):
                        column_list.append(table_item.item(row, column).text())
                    else:
                        column_list.append('')

                content_dic.setdefault(title_list[column], column_list)

            # Write csv
            common_monitor.bprint('Writing ' + str(table_type) + ' table into "' + str(output_file) + '" ...', date_format='%Y-%m-%d %H:%M:%S')

            common_monitor.write_csv(csv_file=output_file, content_dic=content_dic)
# Export table (end) #

    def switch_tab(self, specified_tab):
        """
        Switch to the specified Tab.
        """
        tab_dic = {
                   'MONITOR': self.monitor_tab,
                   'HEARTBEAT': self.heartbeat_tab,
                   'LOG': self.log_tab,
                   'ALARM': self.alarm_tab,
                  }

        self.main_tab.setCurrentWidget(tab_dic[specified_tab])


################
# Main Process #
################
def main():
    (specified_tab) = read_args()
    app = QApplication(sys.argv)
    mw = MainWindow(specified_tab)
    mw.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
