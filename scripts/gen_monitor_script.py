# -*- coding: utf-8 -*-

import os
import sys
import getpass
import datetime


def check_args():
    # Make sure cpython have only one argument.
    if len(sys.argv) != 2:
        print('*Error*: Wrong argument!')
        usage()
        sys.exit(1)
    elif sys.argv[1] in ['-h', '-help', 'help']:
        usage()
        sys.exit(0)


def usage():
    # Print the cpython usage.
    print('Usage:')
    print('    gen_monitor_script <script_name>')


def gen_python_script():
    """
    Generate executable python script.
    """
    script_name = sys.argv[1]

    if os.path.exists(script_name):
        print('*Error*: Python file "' + str(script_name) + '" exists, please remove it first!')
        sys.exit(1)

    (dir_name, base_name) = os.path.split(script_name)

    if dir_name != '':
        if not os.path.exists(dir_name):
            os.mkdirs(dir_name)

    user = getpass.getuser()
    current_time = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')

    try:
        with open(script_name, 'w') as PF:
            PF.write('#!' + str(sys.executable) + '\n')
            PF.write('# -*- coding: utf-8 -*-\n')
            PF.write('################################\n')
            PF.write('# File Name   : ' + str(script_name) + '\n')
            PF.write('# Author      : ' + str(user) + '\n')
            PF.write('# Created On  : ' + str(current_time) + '\n')
            PF.write('# Description :\n')
            PF.write('################################\n')
            PF.write('import os\n')
            PF.write('import re\n')
            PF.write('import sys\n')
            PF.write('import argparse\n')
            PF.write('\n')
            PF.write("os.environ['PYTHONUNBUFFERED'] = '1'\n")
            PF.write("os.environ['MONITOR_VIEWER_INSTALL_PATH'] = '" + str(os.environ['MONITOR_VIEWER_INSTALL_PATH']) + "'\n")
            PF.write('\n')
            PF.write("sys.path.append(str(os.environ['MONITOR_VIEWER_INSTALL_PATH']) + '/common')\n")
            PF.write('import common_monitor\n')
            PF.write('\n')
            PF.write("save_log_ins = common_monitor.SaveLog(\n")
            PF.write("    direction='',\n")
            PF.write("    monitor_item='',\n")
            PF.write("    script_path=os.path.abspath(__file__),\n")
            PF.write("    script_auther='" + str(user) + "',\n")
            PF.write("    script_startup_method='',\n")
            PF.write("    script_execute_frequency='',\n")
            PF.write("    alarm_receivers='',\n")
            PF.write("    alarm_frequency='everytime')\n")
            PF.write('\n')
            PF.write('\n')
            PF.write('def read_args():\n')
            PF.write('    """\n')
            PF.write('    Read in arguments.\n')
            PF.write('    """\n')
            PF.write('    parser = argparse.ArgumentParser()\n')
            PF.write('\n')
            PF.write("    parser.add_argument('-e', '--example',\n")
            PF.write("                        default='',\n")
            PF.write("                        help='This is an example argument.')\n")
            PF.write('\n')
            PF.write('    args = parser.parse_args()\n')
            PF.write('\n')
            PF.write('    return args.example\n')
            PF.write('\n')
            PF.write('\n')
            PF.write('################\n')
            PF.write('# Main Process #\n')
            PF.write('################\n')
            PF.write('def main():\n')
            PF.write('    (example) = read_args()\n')
            PF.write('\n')
            PF.write('\n')
            PF.write("if __name__ == '__main__':\n")
            PF.write('    main()\n')
    except Exception as error:
        print('*Error*: Failed on opening "' + str(script_name) + '" for write: ' + str(error))
        sys.exit(1)

    try:
        # Open permission for crated python file.
        os.chmod(script_name, 0o755)
    except Exception as error:
        print('*Error*: Failed on changing file permission for "' + str(script_name) + '": ' + str(error))
        sys.exit(1)


################
# Main Process #
################
def main():
    check_args()
    gen_python_script()


if __name__ == '__main__':
    main()
