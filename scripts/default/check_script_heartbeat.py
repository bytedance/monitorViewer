# -*- coding: utf-8 -*-

import os
import sys
import datetime

os.environ['PYTHONUNBUFFERED'] = '1'

sys.path.append(str(os.environ['MONITOR_VIEWER_INSTALL_PATH']) + '/common')
import common_monitor
sys.path.append(str(os.environ['MONITOR_VIEWER_INSTALL_PATH']) + '/config')
import config

save_log_ins = common_monitor.SaveLog(
    direction='default',
    monitor_item='check_script_heartbeat',
    script_path=os.path.abspath(__file__),
    script_auther='',
    script_startup_method='crontab',
    script_execute_frequency='once a day',
    alarm_receivers='',
    alarm_frequency='max 1 times')


def check_script_heartbeat():
    """
    Check if the script heartbeat log is continuous.
    """
    if (not config.db_path) or (not os.path.exists(config.db_path)):
        common_monitor.bprint('', level='Error')
        sys.exit(1)

    alarm_title = 'Default Alarm: 心跳日志中断!'
    today = datetime.datetime.now().strftime('%Y%m%d')
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y%m%d')

    for direction in os.listdir(config.db_path):
        direction_path = str(config.db_path) + '/' + str(direction)

        if os.path.exists(direction_path) and os.path.isdir(direction_path):
            for monitor_item in os.listdir(direction_path):
                monitor_item_path = str(direction_path) + '/' + str(monitor_item)

                for dir_name in os.listdir(monitor_item_path):
                    dir_path = str(monitor_item_path) + '/' + str(dir_name)

                    if (dir_name == 'heartbeat') and os.path.isdir(dir_path):
                        log_name_list = list(os.listdir(dir_path))

                        if len(log_name_list) and (today not in log_name_list) and (yesterday not in log_name_list):
                            alarm_message = '针对' + str(direction) + '方向的监控项' + str(monitor_item) + ', 心跳日志已经中断超过一天, 请检查服务是否未正常启动.'
                            save_log_ins.send_alarm(message=alarm_message, alarm_title=alarm_title)


################
# Main Process #
################
def main():
    check_script_heartbeat()


if __name__ == '__main__':
    main()
