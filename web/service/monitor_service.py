import os
import re
import sys
import yaml
import json
import logging
from datetime import datetime, timedelta
from tools.decorator_helper import print_execution_time

sys.path.append(os.environ['MONITOR_VIEWER_INSTALL_PATH'])
from config import config


class MonitorService:
    def __init__(self):
        pass

    def get_direction_list(self) -> list:
        return list(config.valid_direction_dic.keys())

    def get_monitor_item_list(self, direction) -> list:
        if direction is None:
            logging.warning("direction is None")
            return []

        direction_path = f"{config.db_path}/{direction}"

        if not os.path.exists(direction_path):
            logging.warning(f"direction path not exists: {direction_path}")
            return []

        if not os.path.isdir(direction_path):
            logging.warning(f"direction path is not a directory: {direction_path}")
            return []

        return os.listdir(direction_path)

    @print_execution_time
    def get_logs_trend_data(self, begin_date, end_date):
        return self.get_monitor_item_list(None)

    @print_execution_time
    def get_top_alarms_per_monitor_item(self, begin_date, end_date):
        """
        :rtype: list(monitor_item_name, alarm_count)
        """
        filtered_alarm_data = self.get_all_alarm_table_data(begin_date, end_date)
        top_alarm_dict = {}

        for alarm in filtered_alarm_data:
            if alarm['monitor_item'] not in top_alarm_dict:
                top_alarm_dict[alarm['monitor_item']] = 1
            else:
                top_alarm_dict[alarm['monitor_item']] += 1

        sorted_items = sorted(top_alarm_dict.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:10]

    def get_monitor_chart_data(self, begin_date, end_date):
        directions = self.get_direction_list()
        series_datas = []

        for direction in directions:
            monitor_items = self.get_monitor_item_list(direction)
            series_datas.append({
                'name': direction,
                'data': [len(monitor_items)]
            })

        return directions, series_datas

    @print_execution_time
    def get_alarm_chart_data(self, begin_date, end_date):
        directions = self.get_direction_list()
        filtered_alarm_data = self.get_all_alarm_table_data(begin_date, end_date)
        categories = self.get_all_date(begin_date, end_date)
        series_datas = []

        for direction in directions:
            series_data_single_direction = []

            for chart_date in categories:
                alarm_count_per_dir_date = 0

                for alarm in filtered_alarm_data:
                    alarm_time = alarm['time'].replace('-', '')[:9].strip()

                    if alarm_time == chart_date and alarm['direction'] == direction:
                        alarm_count_per_dir_date += 1

                series_data_single_direction.append(alarm_count_per_dir_date)

            series_datas.append({
                'name': direction,
                'data': series_data_single_direction
            })

        return categories, series_datas

    @print_execution_time
    def get_alarm_count(self, begin_date, end_date):
        return len(self.get_all_alarm_table_data(begin_date, end_date))

    @print_execution_time
    def get_monitor_count(self):
        return len(self.get_monitor_table_data())

    @print_execution_time
    def get_error_log_count(self, begin_date, end_date):
        all_logs = self.get_all_log_table_data(begin_date, end_date)
        error_log_count = 0

        for log in all_logs:
            if log['message_level'] == 'Error':
                error_log_count += 1

        return error_log_count

    @print_execution_time
    def get_all_log_table_data(self, begin_date, end_date):
        directions = self.get_direction_list()
        monitor_items = {}
        log_table_data = []

        for direction in directions:
            monitor_items[direction] = self.get_monitor_item_list(direction)

            for monitor_item in monitor_items[direction]:
                log_data = self.get_log_table_data(begin_date, end_date, direction, monitor_item)
                log_table_data.extend(log_data)

        return log_table_data

    @print_execution_time
    def get_all_alarm_table_data(self, begin_date, end_date):
        directions = self.get_direction_list()
        monitor_items = {}
        alarm_table_data = []

        for direction in directions:
            monitor_items[direction] = self.get_monitor_item_list(direction)

            for monitor_item in monitor_items[direction]:
                alarm_data = self.get_alarm_table_data(begin_date, end_date, direction, monitor_item)
                alarm_table_data.extend(alarm_data)

        return alarm_table_data

    @print_execution_time
    def get_all_heartbeat_table_data(self, begin_date, end_date):
        directions = self.get_direction_list()
        monitor_items = {}
        heartbeat_table_data = []

        for direction in directions:
            monitor_items[direction] = self.get_monitor_item_list(direction)

            for monitor_item in monitor_items[direction]:
                heartbeat_data = self.get_heartbeat_table_data(begin_date, end_date, direction, monitor_item)
                heartbeat_table_data.extend(heartbeat_data)

        return heartbeat_table_data

    @print_execution_time
    def get_heartbeat_table_data(self, begin_datetime, end_datetime, direction, monitor_item):
        begin_date = begin_datetime[:11].replace('-', '')
        end_date = end_datetime[:11].replace('-', '')
        heartbeat_table_data = []

        if direction not in config.valid_direction_dic:
            return heartbeat_table_data

        if not os.path.exists(f"{config.db_path}/{direction}/{monitor_item}/heartbeat"):
            return heartbeat_table_data

        for date_file_name in os.listdir(f"{config.db_path}/{direction}/{monitor_item}/heartbeat"):
            if ((begin_datetime is not None and self.compare_date(date_file_name, begin_date) == -1) or
                    (end_datetime is not None and self.compare_date(date_file_name, end_date) == 1) or
                    not re.match(r'^\d{8}$', date_file_name)):

                continue

            with open(f"{config.db_path}/{direction}/{monitor_item}/heartbeat/{date_file_name}", 'r') as f:
                for line in f.readlines():
                    heartbeat_info_dic = json.loads(line.strip())
                    time = heartbeat_info_dic['time']

                    if self.compare_time(time, begin_datetime) == -1:
                        continue

                    if self.compare_time(time, end_datetime) == 1:
                        continue

                    heartbeat_info_dic.setdefault('direction', direction)
                    heartbeat_info_dic.setdefault('monitor_item', monitor_item)
                    heartbeat_table_data.append(heartbeat_info_dic)

        return heartbeat_table_data

    @print_execution_time
    def get_log_table_data(self, begin_datetime, end_datetime, direction, monitor_item):
        begin_date = begin_datetime[:11].replace('-', '')
        end_date = end_datetime[:11].replace('-', '')
        log_table_data = []

        if direction not in config.valid_direction_dic:
            return log_table_data

        if not os.path.exists(f"{config.db_path}/{direction}/{monitor_item}/log"):
            return log_table_data

        for date_file_name in os.listdir(f"{config.db_path}/{direction}/{monitor_item}/log"):
            if ((begin_datetime is not None and self.compare_date(date_file_name, begin_date) == -1) or
                    (end_datetime is not None and self.compare_date(date_file_name, end_date) == 1) or
                    not re.match(r'^\d{8}$', date_file_name)):

                continue

            with open(f"{config.db_path}/{direction}/{monitor_item}/log/{date_file_name}", 'r') as f:
                for line in f.readlines():
                    log_info_dic = json.loads(line.strip())
                    time = log_info_dic['time']

                    if self.compare_time(time, begin_datetime) == -1:
                        continue

                    if self.compare_time(time, end_datetime) == 1:
                        continue

                    log_info_dic['message'] = re.sub(r'\n', '; ', log_info_dic['message'])
                    log_info_dic.setdefault('direction', direction)
                    log_info_dic.setdefault('monitor_item', monitor_item)
                    log_table_data.append(log_info_dic)

        return log_table_data

    @print_execution_time
    def get_alarm_table_data(self, begin_datetime, end_datetime, direction, monitor_item):
        begin_date = begin_datetime[:11].replace('-', '')
        end_date = end_datetime[:11].replace('-', '')
        alarm_table_data = []

        if direction not in config.valid_direction_dic:
            return alarm_table_data

        if not os.path.exists(f"{config.db_path}/{direction}/{monitor_item}/alarm"):
            return alarm_table_data

        for date_file_name in os.listdir(f"{config.db_path}/{direction}/{monitor_item}/alarm"):
            if ((begin_datetime is not None and self.compare_date(date_file_name, begin_date) == -1) or
                    (end_datetime is not None and self.compare_date(date_file_name, end_date) == 1) or
                    not re.match(r'^\d{8}$', date_file_name)):

                continue

            with open(f"{config.db_path}/{direction}/{monitor_item}/alarm/{date_file_name}", 'r') as f:
                for line in f.readlines():
                    alarm_info_dic = json.loads(line.strip())
                    time = alarm_info_dic['time']

                    if self.compare_time(time, begin_datetime) == -1:
                        continue

                    if self.compare_time(time, end_datetime) == 1:
                        continue

                    alarm_info_dic['message'] = re.sub(r'\n', '; ', alarm_info_dic['message'])
                    alarm_info_dic.setdefault('direction', direction)
                    alarm_info_dic.setdefault('monitor_item', monitor_item)
                    alarm_table_data.append(alarm_info_dic)

        return alarm_table_data

    @print_execution_time
    def get_monitor_table_data(self):
        monitor_table_data = []

        for direction in config.valid_direction_dic.keys():
            if not os.path.exists(f"{config.db_path}/{direction}"):
                continue

            for monitor_item in os.listdir(f"{config.db_path}/{direction}"):
                if not os.path.exists(f"{config.db_path}/{direction}/{monitor_item}/monitor_item.yaml"):
                    continue

                with open(f"{config.db_path}/{direction}/{monitor_item}/monitor_item.yaml", 'r') as f:
                    monitor_info = yaml.load(f, Loader=yaml.FullLoader)
                    monitor_item_data = {}

                    if 'direction_admin' in monitor_info.keys():
                        monitor_item_data['admin'] = monitor_info['direction_admin']

                    if 'script_startup_method' in monitor_info.keys():
                        monitor_item_data['startup'] = monitor_info['script_startup_method']

                    if 'script_startup_host' in monitor_info.keys():
                        monitor_item_data['host'] = monitor_info['script_startup_host']

                    if 'script_execute_frequency' in monitor_info.keys():
                        monitor_item_data['exec_frequency'] = monitor_info['script_execute_frequency']

                    if 'alarm_frequency' in monitor_info.keys():
                        monitor_item_data['alarm_frequency'] = monitor_info['alarm_frequency']

                    if 'script_path' in monitor_info.keys():
                        monitor_item_data['script'] = monitor_info['script_path'] + '.'

                    monitor_item_data['direction'] = direction
                    monitor_item_data['item'] = monitor_item
                    monitor_table_data.append(monitor_item_data)

        return monitor_table_data

    def compare_time(self, time1, time2) -> int:
        date_time1 = datetime.strptime(time1.strip(), '%Y-%m-%d %H:%M:%S')
        date_time2 = datetime.strptime(time2.strip(), '%Y-%m-%d %H:%M:%S')

        # 比较两个 datetime 对象的大小
        if date_time1 < date_time2:
            return -1
        elif date_time1 > date_time2:
            return 1
        else:
            return 0

    def compare_date(self, date1, date2) -> int:
        date_time1 = datetime.strptime(date1.strip(), '%Y%m%d')
        date_time2 = datetime.strptime(date2.strip(), '%Y%m%d')

        # 比较两个 datetime 对象的大小
        if date_time1 < date_time2:
            return -1
        elif date_time1 > date_time2:
            return 1
        else:
            return 0

    def get_all_date(self, begin_datetime, end_datetime):
        begin_time = datetime.strptime(begin_datetime.strip(), '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(end_datetime.strip(), '%Y-%m-%d %H:%M:%S')
        dates = []
        current_date = begin_time.date()
        end_date = end_time.date()

        while current_date <= end_date:
            dates.append(current_date.strftime("%Y%m%d"))
            current_date += timedelta(days=1)

        return dates
