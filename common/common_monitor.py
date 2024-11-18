import os
import re
import sys
import json
import yaml
import copy
import pandas
import socket
import getpass
import hashlib
import datetime
import subprocess


class SaveLog():
    """
    SaveLog is used for monitor system, has two main functions:
    * Save specified message into database.
    * Send alarm.
    """
    def __init__(self, direction='', monitor_item='', script_path='', script_auther='', script_startup_method='', script_startup_host='', script_execute_frequency='', alarm_receivers='', alarm_frequency='everytime'):
        """
        Below are initialization arguments:
        [direction]:                Specify businees direction, default is "default", must have been defined on variable "valid_direction_dic" on config.py.
        [direction_admin]:          Hidden argument, defined on variable "valid_direction_dic" on config.py.
        [monitor_item]:             Required argument, description of the monitor item, must be a string without space.
        [script_path]:              Specify script path, suggest use "os.path.abspath(__file__)".
        [script_auther]:            Specify script auther, default is current user.
        [script_startup_method]:    Specify script startup method, usually be "crontab" or "jenkins".
        [script_startup_host]:      Hidden argument, specify where the script is executed on, default is current host.
        [script_execute_frequency]: Description of execute frequency, for example, "every 5 minutes".
        [alarm_receivers]:          Specify alarm receivers, default is direction_admin.
        [alarm_frequency]:          Specify alarm frequency, support "everytime" and "max <n> times", default is "everytime".
        """
        # Get variable settings from config file
        self.config_dic = self.get_config_setting()

        # Check direction
        if not direction:
            self.print_warning('No direction is specified, will set it to "default".')
            direction = 'default'

        if direction not in self.config_dic['valid_direction_dic']:
            self.print_error('"' + str(direction) + '": Invalid direction, missing on valid_direction_dic of config/config.py.')

        # Check monitor_item
        if not monitor_item:
            self.print_error('Required argument "monitor_item" is not specified.')

        if re.search(r' ', monitor_item):
            self.print_error('"' + str(monitor_item) + '": Invalid "monitor_item" setting, should not contain spaces.')

        # Get monitor_item informaiton from monitor_item yaml file
        old_monitor_item_dic = self.read_monitor_item_yaml(direction, monitor_item)
        self.monitor_item_dic = copy.deepcopy(old_monitor_item_dic)

        # Check script_path
        if script_path:
            if os.path.exists(script_path):
                if ('script_path' not in self.monitor_item_dic) or (self.monitor_item_dic['script_path'] != script_path):
                    self.monitor_item_dic['script_path'] = script_path
            else:
                self.print_warning('"' + str(script_path) + '": Not find such script_path.')
        else:
            if 'script_path' not in self.monitor_item_dic:
                self.print_warning('No script_path is specified.')

        # Check script_auther
        if script_auther:
            if ('script_auther' not in self.monitor_item_dic) or (self.monitor_item_dic['script_auther'] != script_auther):
                self.monitor_item_dic['script_auther'] = script_auther
        else:
            if 'script_auther' not in self.monitor_item_dic:
                current_user = getpass.getuser()
                self.print_warning('No script_auther is specified, will take current user "' + str(current_user) + '" as the script_auther.')
                self.monitor_item_dic['script_auther'] = current_user

        # Check script_startup_method
        if script_startup_method:
            if ('script_startup_method' not in self.monitor_item_dic) or (self.monitor_item_dic['script_startup_method'] != script_startup_method):
                self.monitor_item_dic['script_startup_method'] = script_startup_method
        else:
            if 'script_startup_method' not in self.monitor_item_dic:
                self.print_warning('No script_startup_method is specified.')

        # Set script_startup_host
        script_startup_host = socket.gethostbyname(socket.gethostname())

        if ('script_startup_host' not in self.monitor_item_dic) or (self.monitor_item_dic['script_startup_host'] != script_startup_host):
            self.monitor_item_dic['script_startup_host'] = script_startup_host

        # Check script_execute_frequency
        if script_execute_frequency:
            if ('script_execute_frequency' not in self.monitor_item_dic) or (self.monitor_item_dic['script_execute_frequency'] != script_execute_frequency):
                self.monitor_item_dic['script_execute_frequency'] = script_execute_frequency
        else:
            if 'script_execute_frequency' not in self.monitor_item_dic:
                self.print_warning('No script_execute_frequency is specified.')

        # Check alarm_receivers
        if alarm_receivers:
            if ('alarm_receivers' not in self.monitor_item_dic) or (self.monitor_item_dic['alarm_receivers'] != alarm_receivers):
                self.monitor_item_dic['alarm_receivers'] = alarm_receivers
        else:
            if 'alarm_receivers' not in self.monitor_item_dic:
                self.print_warning('No alarm_receivers is specified, will set direction_admin as the default alarm receivers.')
                self.monitor_item_dic['alarm_receivers'] = self.config_dic['valid_direction_dic'][direction]

        # Check alarm_frequency
        if alarm_frequency:
            if ('alarm_frequency' not in self.monitor_item_dic) or (self.monitor_item_dic['alarm_frequency'] != alarm_frequency):
                self.monitor_item_dic['alarm_frequency'] = alarm_frequency
        else:
            if 'alarm_frequency' not in self.monitor_item_dic:
                self.print_warning('No alarm_frequency is specified.')

        # Create direction directory.
        self.create_direction_dir(direction)

        # Update monitor_item yaml file
        if self.monitor_item_dic != old_monitor_item_dic:
            self.write_monitor_item_yaml(direction, monitor_item)

        # Heartbeat registration
        self.heartbeat_registration(direction, monitor_item)

    def print_warning(self, message):
        """
        Print warning message with bprint.
        """
        bprint('[SaveLog] ' + str(message), level='Warning')

    def print_error(self, message):
        """
        Print error message with bprint, then exit 1.
        """
        bprint('[SaveLog] ' + str(message), level='Error')
        sys.exit(1)

    def get_config_setting(self):
        """
        Get variable settings fron config.py.
        """
        config_dic = {}
        config_dir = str(os.environ['MONITOR_VIEWER_INSTALL_PATH']) + '/config'
        config_file = str(config_dir) + '/config.py'

        if not os.path.exists(config_file):
            self.print_error('"' + str(config_file) + '": No such config file.')

        sys.path.insert(0, config_dir)
        import config

        for var in dir(config):
            if not re.match(r'^_.*$', var):
                config_dic[var] = getattr(config, var)

        # Check configuration integrity
        if 'valid_direction_dic' not in config_dic:
            self.print_error('Required configuration variable "valid_direction_dic" is missing.')
        elif not config_dic['valid_direction_dic']:
            self.print_error('Required configuration variable "valid_direction_dic" is empty.')

        if 'db_path' not in config_dic:
            self.print_error('Required configuration variable "db_path" is missing.')
        elif not config_dic['db_path']:
            self.print_error('Required configuration variable "db_path" is empty.')
        elif not os.path.exists(config_dic['db_path']):
            self.print_error('"' + str(config_dic['db_path']) + '": No such database path.')

        if 'valid_message_level_list' not in config_dic:
            self.print_error('Required configuration variable "valid_message_level_list" is missing.')
        elif not config_dic['valid_message_level_list']:
            self.print_error('Required configuration variable "valid_message_level_list" is empty.')

        if 'send_alarm_command' not in config_dic:
            self.print_error('Required configuration variable "send_alarm_command" is missing.')
        elif not config_dic['send_alarm_command']:
            self.print_error('Required configuration variable "send_alarm_command" is empty.')

        return config_dic

    def read_monitor_item_yaml(self, direction, monitor_item):
        """
        Get monitor item information from <db_path>/<direction>/<monitor_item>/monitor_item.yaml
        """
        monitor_item_dic = {}
        monitor_item_file = str(self.config_dic['db_path']) + '/' + str(direction) + '/' + str(monitor_item) + '/monitor_item.yaml'

        if os.path.exists(monitor_item_file):
            with open(monitor_item_file, 'r') as MIF:
                monitor_item_dic = yaml.load(MIF, Loader=yaml.FullLoader)

        # Set default value
        monitor_item_dic['direction'] = direction
        monitor_item_dic['direction_admin'] = self.config_dic['valid_direction_dic'][direction]
        monitor_item_dic['monitor_item'] = monitor_item

        return monitor_item_dic

    def create_direction_dir(self, direction):
        """
        Create direction dir with access permission 777.
        """
        direction_dir = str(self.config_dic['db_path']) + '/' + str(direction)

        if not os.path.exists(direction_dir):
            try:
                os.makedirs(direction_dir)
                os.chmod(direction_dir, 0o777)
            except Exception as error:
                self.print_error('Failed on creating direction directory "' + str(direction_dir) + '", ' + str(error))

    def write_monitor_item_yaml(self, direction, monitor_item):
        """
        Write monitor item information into <db_path>/<direction>/<monitor_item>/monitor_item.yaml
        """
        # Create monitor_item directory.
        monitor_item_dir = str(self.config_dic['db_path']) + '/' + str(direction) + '/' + str(monitor_item)

        if not os.path.exists(monitor_item_dir):
            os.makedirs(monitor_item_dir)
            os.chmod(monitor_item_dir, 0o755)

        # Save self.monitor_item_dic into monitor_item_file.
        monitor_item_file = str(monitor_item_dir) + '/monitor_item.yaml'

        with open(monitor_item_file, 'w') as MIF:
            MIF.write(yaml.dump(self.monitor_item_dic, allow_unicode=True))

    def heartbeat_registration(self, direction, monitor_item):
        """
        Register in the registration file when class "SaveLog" is initialized.
        """
        # Create heartbeat log directory.
        heartbeat_log_dir = str(self.config_dic['db_path']) + '/' + str(direction) + '/' + str(monitor_item) + '/heartbeat'

        if not os.path.exists(heartbeat_log_dir):
            os.makedirs(heartbeat_log_dir)
            os.chmod(heartbeat_log_dir, 0o755)

        # Save specified message into log file.
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        heartbeat_log_file = str(heartbeat_log_dir) + '/' + str(current_date)
        current_user = getpass.getuser()

        with open(heartbeat_log_file, 'a') as HLF:
            heartbeat_info_dic = {"time": current_time, "user": current_user, "host": self.monitor_item_dic['script_startup_host'], "script": self.monitor_item_dic['script_path']}
            HLF.write(str(json.dumps(heartbeat_info_dic, ensure_ascii=False)) + '\n')

    def save_log(self, message, message_level='Warning', print_mode=True):
        """
        Save script log message into log file under <db_path>/<direction>/<monitor_item>/log.
        """
        # Check message_level.
        if message_level not in self.config_dic['valid_message_level_list']:
            self.print_error('"' + str(message_level) + '": Invalid message_level, it must be in "' + str('/'.join(self.config_dic['valid_message_level_list'])) + '".')

        # Create log directory.
        log_dir = str(self.config_dic['db_path']) + '/' + str(self.monitor_item_dic['direction']) + '/' + str(self.monitor_item_dic['monitor_item']) + '/log'

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            os.chmod(log_dir, 0o755)

        # Save specified message into log file.
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file = str(log_dir) + '/' + str(current_date)

        with open(log_file, 'a') as LF:
            log_info_dic = {"time": current_time, "message_level": message_level, "message": message}
            LF.write(str(json.dumps(log_info_dic, ensure_ascii=False)) + '\n')

        if print_mode:
            if message_level in ['Debug', 'Info', 'Warning', 'Error', 'Fatal']:
                bprint(message, level=message_level)
            else:
                print(message)

    def send_alarm(self, message, alarm_title='', alarm_receivers='', alarm_frequency=''):
        """
        Send alarm to alarm_receivers, and save the alarm behavior.
        """
        if not alarm_title:
            alarm_title = self.monitor_item_dic['monitor_item']

        if not alarm_receivers:
            alarm_receivers = self.monitor_item_dic['alarm_receivers']

        if not alarm_frequency:
            alarm_frequency = self.monitor_item_dic['alarm_frequency']

        if self.check_alarm_frequency(message, alarm_receivers, alarm_frequency):
            send_alarm_command = self.config_dic['send_alarm_command']
            send_alarm_command = re.sub(r'<TITLE>', alarm_title, send_alarm_command)
            send_alarm_command = re.sub(r'<MESSAGE>', message, send_alarm_command)
            send_alarm_command = re.sub(r'<RECEIVERS>', alarm_receivers, send_alarm_command)
            (return_code, stdout, stderr) = run_command(send_alarm_command)

            if return_code == 0:
                self.save_alarm_log(message, alarm_receivers, result='PASSED')
            else:
                self.save_alarm_log(message, alarm_receivers, result='FAILED')

    def check_alarm_frequency(self, message, alarm_receivers, alarm_frequency):
        """
        Make sure alarm or not.
        """
        if re.search(r'everytime', alarm_frequency):
            pass
        elif re.match(r'^\s*max\s+(\d+)\s+times\s*$', alarm_frequency):
            my_match = re.match(r'^\s*max\s+(\d+)\s+times\s*$', alarm_frequency)
            max_alarm_num = int(my_match.group(1))

            # Get today alarm num
            alarm_num = 0
            current_date = datetime.datetime.now().strftime('%Y%m%d')
            alarm_log_file = str(self.config_dic['db_path']) + '/' + str(self.monitor_item_dic['direction']) + '/' + str(self.monitor_item_dic['monitor_item']) + '/alarm/' + str(current_date)
            receivers_message = str(alarm_receivers) + ' ' + str(message)
            md5 = hashlib.md5(receivers_message.encode()).hexdigest()

            if os.path.exists(alarm_log_file):
                with open(alarm_log_file, 'r') as ALF:
                    for line in ALF.readlines():
                        alarm_info_dic = json.loads(line.strip())

                        if alarm_info_dic['md5'] == md5:
                            alarm_num += 1

            if alarm_num >= max_alarm_num:
                self.print_warning('It have reached the max alarm limitation, will not send alarm any more today.')
                return False
        else:
            self.print_warning('"' + str(alarm_frequency) + '": Invalid alarm_frequency setting, will not send alarm.')
            return False

        return True

    def save_alarm_log(self, message, alarm_receivers, result='PASSED'):
        """
        Save script alarm message into alarm log file under <db_path>/<direction>/<monitor_item>/alarm.
        """
        # Create alarm log directory.
        alarm_log_dir = str(self.config_dic['db_path']) + '/' + str(self.monitor_item_dic['direction']) + '/' + str(self.monitor_item_dic['monitor_item']) + '/alarm'

        if not os.path.exists(alarm_log_dir):
            os.makedirs(alarm_log_dir)
            os.chmod(alarm_log_dir, 0o755)

        # Save specified message into alarm log file.
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        alarm_log_file = str(alarm_log_dir) + '/' + str(current_date)
        receivers_message = str(alarm_receivers) + ' ' + str(message)
        md5 = hashlib.md5(receivers_message.encode()).hexdigest()

        with open(alarm_log_file, 'a') as LF:
            alarm_info_dic = {"time": current_time, "md5": md5, "receivers": alarm_receivers, "send_alarm_result": result, "message": message}
            LF.write(str(json.dumps(alarm_info_dic, ensure_ascii=False)) + '\n')


def bprint(message, color='', background_color='', display_method='', date_format='', level='', indent=0, end='\n', save_file='', save_file_method='a'):
    """
    Enhancement of "print" function.

    color:            Specify font foreground color, default to follow the terminal settings.
    background_color: Specify font background color, default to follow the terminal settings.
    display_method:   Specify font display method, default to follow the terminal settings.
    date_format:      Will show date/time information before the message, such as "%Y_%m_%d %H:%M:%S". Default is "", means silent mode.
    level:            Will show message level information after date/time information, default is "", means show nothing.
    indent:           How much spaces to indent for specified message (with level information), default is 0, means no indentation.
    end:              Specify the character at the end of the output, default is "\n".
    save_file:        Save message into specified file, default is "", means save nothing.
    save_file_method: Save message with "append" or "write" mode, default is "append" mode.

    For "color" and "background_color":
    -----------------------------------------------
    字体色   |   背景色   |   Color    |   颜色描述
    -----------------------------------------------
    30       |   40       |   black    |   黑色
    31       |   41       |   red      |   红色
    32       |   42       |   green    |   绿色
    33       |   43       |   yellow   |   黃色
    34       |   44       |   blue     |   蓝色
    35       |   45       |   purple   |   紫色
    36       |   46       |   cyan     |   青色
    37       |   47       |   white    |   白色
    -----------------------------------------------

    For "display_method":
    ---------------------------
    显示方式   |   效果
    ---------------------------
    0          |   终端默认设置
    1          |   高亮显示
    4          |   使用下划线
    5          |   闪烁
    7          |   反白显示
    8          |   不可见
    ---------------------------

    For "level":
    -------------------------------------------------------------
    层级      |   说明
    -------------------------------------------------------------
    Debug     |   程序运行的详细信息, 主要用于调试.
    Info      |   程序运行过程信息, 主要用于将系统状态反馈给用户.
    Warning   |   表明会出现潜在错误, 但是一般不影响系统继续运行.
    Error     |   发生错误, 不确定系统是否可以继续运行.
    Fatal     |   发生严重错误, 程序会停止运行并退出.
    -------------------------------------------------------------

    For "save_file_method":
    -----------------------------------------------------------
    模式   |   说明
    -----------------------------------------------------------
    a      |   append mode, append content to existing file.
    w      |   write mode, create a new file and write content.
    -----------------------------------------------------------
    """
    # Check arguments.
    color_dic = {'black': 30,
                 'red': 31,
                 'green': 32,
                 'yellow': 33,
                 'blue': 34,
                 'purple': 35,
                 'cyan': 36,
                 'white': 37}

    if color:
        if (color not in color_dic.keys()) and (color not in color_dic.values()):
            bprint('*Warning* (bprint): Meet some setting problem with below message.', date_format='', color=33, display_method=1)
            bprint('                    ' + str(message), date_format='', color=33, display_method=1)
            bprint('*Warning* (bprint): "' + str(color) + '": Invalid color setting, it must follow below rules.', date_format='', color=33, display_method=1)
            bprint('''
                    ----------------------------------
                    字体色   |   Color    |   颜色描述
                    ----------------------------------
                    30       |   black    |   黑色
                    31       |   red      |   红色
                    32       |   green    |   绿色
                    33       |   yellow   |   黃色
                    34       |   blue     |   蓝色
                    35       |   purple   |   紫色
                    36       |   cyan     |   青色
                    37       |   white    |   白色
                    ----------------------------------
            ''', date_format='', color=33, display_method=1)

            return

    background_color_dic = {'black': 40,
                            'red': 41,
                            'green': 42,
                            'yellow': 43,
                            'blue': 44,
                            'purple': 45,
                            'cyan': 46,
                            'white': 47}

    if background_color:
        if (background_color not in background_color_dic.keys()) and (background_color not in background_color_dic.values()):
            bprint('*Warning* (bprint): Meet some setting problem with below message.', date_format='', color=33, display_method=1)
            bprint('                    ' + str(message), date_format='', color=33, display_method=1)
            bprint('*Warning* (bprint): "' + str(background_color) + '": Invalid background_color setting, it must follow below rules.', date_format='', color=33, display_method=1)
            bprint('''
                    ----------------------------------
                    背景色   |   Color    |   颜色描述
                    ----------------------------------
                    40       |   black    |   黑色
                    41       |   red      |   红色
                    42       |   green    |   绿色
                    43       |   yellow   |   黃色
                    44       |   blue     |   蓝色
                    45       |   purple   |   紫色
                    46       |   cyan     |   青色
                    47       |   white    |   白色
                    ----------------------------------
            ''', date_format='', color=33, display_method=1)

            return

    if display_method:
        valid_display_method_list = [0, 1, 4, 5, 7, 8]

        if display_method not in valid_display_method_list:
            bprint('*Warning* (bprint): Meet some setting problem with below message.', date_format='', color=33, display_method=1)
            bprint('                    ' + str(message), date_format='', color=33, display_method=1)
            bprint('*Warning* (bprint): "' + str(display_method) + '": Invalid display_method setting, it must be integer between 0,1,4,5,7,8.', date_format='', color=33, display_method=1)
            bprint('''
                    ----------------------------
                    显示方式   |    效果
                    ----------------------------
                    0          |    终端默认设置
                    1          |    高亮显示
                    4          |    使用下划线
                    5          |    闪烁
                    7          |    反白显示
                    8          |    不可见
                    ----------------------------
            ''', date_format='', color=33, display_method=1)

            return

    if level:
        valid_level_list = ['Debug', 'Info', 'Warning', 'Error', 'Fatal']

        if level not in valid_level_list:
            bprint('*Warning* (bprint): Meet some setting problem with below message.', date_format='', color=33, display_method=1)
            bprint('                    ' + str(message), date_format='', color=33, display_method=1)
            bprint('*Warning* (bprint): "' + str(level) + '": Invalid level setting, it must be Debug/Info/Warning/Error/Fatal.', date_format='', color=33, display_method=1)
            bprint('''
                    -------------------------------------------------------------
                    层级      |   说明
                    -------------------------------------------------------------
                    Debug     |   程序运行的详细信息, 主要用于调试.
                    Info      |   程序运行过程信息, 主要用于将系统状态反馈给用户.
                    Warning   |   表明会出现潜在错误, 但是一般不影响系统继续运行.
                    Error     |   发生错误, 不确定系统是否可以继续运行.
                    Fatal     |   发生严重错误, 程序会停止运行并退出.
                    -------------------------------------------------------------
            ''', date_format='', color=33, display_method=1)
            return

    if not re.match(r'^\d+$', str(indent)):
        bprint('*Warning* (bprint): Meet some setting problem with below message.', date_format='', color=33, display_method=1)
        bprint('                    ' + str(message), date_format='', color=33, display_method=1)
        bprint('*Warning* (bprint): "' + str(indent) + '": Invalid indent setting, it must be a positive integer, will reset to "0".', date_format='', color=33, display_method=1)

        indent = 0

    if save_file:
        valid_save_file_method_list = ['a', 'append', 'w', 'write']

        if save_file_method not in valid_save_file_method_list:
            bprint('*Warning* (bprint): Meet some setting problem with below message.', date_format='', color=33, display_method=1)
            bprint('                    ' + str(message), date_format='', color=33, display_method=1)
            bprint('*Warning* (bprint): "' + str(save_file_method) + '": Invalid save_file_method setting, it must be "a" or "w".', date_format='', color=33, display_method=1)
            bprint('''
                    -----------------------------------------------------------
                    模式   |   说明
                    -----------------------------------------------------------
                    a      |   append mode, append content to existing file.
                    w      |   write mode, create a new file and write content.
                    -----------------------------------------------------------
            ''', date_format='', color=33, display_method=1)

            return

    # Set default color/background_color/display_method setting for different levels.
    if level:
        if level == 'Warning':
            if not display_method:
                display_method = 1

            if not color:
                color = 33
        elif level == 'Error':
            if not display_method:
                display_method = 1

            if not color:
                color = 31
        elif level == 'Fatal':
            if not display_method:
                display_method = 1

            if not background_color:
                background_color = 41

            if background_color == 41:
                if not color:
                    color = 37
            else:
                if not color:
                    color = 35

    # Get final color setting.
    final_color_setting = ''

    if color or background_color or display_method:
        final_color_setting = '\033['

        if display_method:
            final_color_setting = str(final_color_setting) + str(display_method)

        if color:
            if not re.match(r'^\d{2}$', str(color)):
                color = color_dic[color]

            if re.match(r'^.*\d$', final_color_setting):
                final_color_setting = str(final_color_setting) + ';' + str(color)
            else:
                final_color_setting = str(final_color_setting) + str(color)

        if background_color:
            if not re.match(r'^\d{2}$', str(background_color)):
                background_color = background_color_dic[background_color]

            if re.match(r'^.*\d$', final_color_setting):
                final_color_setting = str(final_color_setting) + ';' + str(background_color)
            else:
                final_color_setting = str(final_color_setting) + str(background_color)

        final_color_setting = str(final_color_setting) + 'm'

    # Get current_time if date_format is specified.
    current_time = ''

    if date_format:
        try:
            current_time = datetime.datetime.now().strftime(date_format)
        except Exception:
            bprint('*Warning* (bprint): Meet some setting problem with below message.', date_format='', color=33, display_method=1)
            bprint('                    ' + str(message), date_format='', color=33, display_method=1)
            bprint('*Warning* (bprint): "' + str(date_format) + '": Invalid date_format setting, suggest to use the default setting.', date_format='', color=33, display_method=1)
            return

    # Print message with specified format.
    final_message = ''

    if current_time:
        final_message = str(final_message) + '[' + str(current_time) + '] '

    if indent > 0:
        final_message = str(final_message) + ' ' * indent

    if level:
        final_message = str(final_message) + '*' + str(level) + '*: '

    final_message = str(final_message) + str(message)

    if final_color_setting:
        final_message_with_color = final_color_setting + str(final_message) + '\033[0m'
    else:
        final_message_with_color = final_message

    print(final_message_with_color, end=end)

    # Save file.
    if save_file:
        try:
            with open(save_file, save_file_method) as SF:
                SF.write(str(final_message) + '\n')
        except Exception as warning:
            bprint('*Warning* (bprint): Meet some problem when saveing below message into file "' + str(save_file) + '".', date_format='', color=33, display_method=1)
            bprint('                    ' + str(message), date_format='', color=33, display_method=1)
            bprint('*Warning* (bprint): ' + str(warning), date_format='', color=33, display_method=1)
            return


def run_command(command, mystdin=subprocess.PIPE, mystdout=subprocess.PIPE, mystderr=subprocess.PIPE, show=None):
    """
    Run system command with subprocess.Popen, get returncode/stdout/stderr.
    """
    SP = subprocess.Popen(command, shell=True, stdin=mystdin, stdout=mystdout, stderr=mystderr)
    (stdout, stderr) = SP.communicate()

    if show:
        if show == 'stdout':
            print(str(stdout, 'utf-8').strip())
        elif show == 'stderr':
            print(str(stderr, 'utf-8').strip())

    return (SP.returncode, stdout, stderr)


def write_csv(csv_file, content_dic):
    """
    Write csv with content_dic.
    content_dic = {
        'title_1': [column1_1, columne1_2, ...],
        'title_2': [column2_1, columne2_2, ...],
        ...
    }
    """
    df = pandas.DataFrame(content_dic)
    df.to_csv(csv_file, index=False)
