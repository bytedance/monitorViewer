import os
import sys
import getpass

CWD = os.getcwd()
USER = getpass.getuser()
PYTHON_PATH = os.path.dirname(os.path.abspath(sys.executable))


def check_python_version():
    """
    Check python version.
    python3.12.7 is suggested.
    """
    print('>>> Check python version.')

    current_python = sys.version_info[:2]
    required_python = (3, 12)

    if current_python < required_python:
        sys.stderr.write("""
==========================
Unsupported Python version
==========================
lsfMonitor requires Python {}.{},
Current python is Python {}.{}.
""".format(*(required_python + current_python)))
        sys.exit(1)
    else:
        print('    Required python version : ' + str(required_python))
        print('    Current  python version : ' + str(current_python))
        print('')


def gen_shell_tools():
    """
    Generate shell scripts under <MONITOR_VIEWER_INSTALL_PATH>/tools.
    """
    tool_list = ['bin/monitor_viewer', 'scripts/gen_monitor_script', 'scripts/default/check_script_heartbeat', 'tools/patch']

    for tool_name in tool_list:
        tool = str(CWD) + '/' + str(tool_name)
        ld_library_path_setting = 'export LD_LIBRARY_PATH=$MONITOR_VIEWER_INSTALL_PATH/lib:'

        if 'LD_LIBRARY_PATH' in os.environ:
            ld_library_path_setting = str(ld_library_path_setting) + str(os.environ['LD_LIBRARY_PATH'])

        print('>>> Generate script "' + str(tool) + '".')

        try:
            with open(tool, 'w') as SP:
                SP.write("""#!/bin/bash

# Set python3 path.
export PATH=""" + str(PYTHON_PATH) + """:$PATH

# Set install path.
export MONITOR_VIEWER_INSTALL_PATH=""" + str(CWD) + """

# Set LD_LIBRARY_PATH.
""" + str(ld_library_path_setting) + """

# Execute """ + str(tool_name) + """.py.
python3 $MONITOR_VIEWER_INSTALL_PATH/""" + str(tool_name) + '.py $@')

            os.chmod(tool, 0o755)
        except Exception as error:
            print('*Error*: Failed on generating script "' + str(tool) + '": ' + str(error))
            sys.exit(1)


def gen_config_file():
    """
    Generate config files.
    """
    config_file = str(CWD) + '/config/config.py'
    db_path = str(CWD) + '/db'

    # Generate config_file.
    print('>>> Generate config file "' + str(config_file) + '".')

    if os.path.exists(config_file):
        print('    *Warning*: config file "' + str(config_file) + '" already exists, will not update it.')
    else:
        try:
            with open(config_file, 'w') as CF:
                CF.write('''# Specify valid direction and direction_admin.
valid_direction_dic = {
    "default": "''' + str(USER) + '''",
}

# Specify database path.
db_path = "''' + str(db_path) + '''"

# Specify valid message level list, which is used on SaveLog.save_log argument.
valid_message_level_list = ['Debug', 'Info', 'Warning', 'Error', 'Fatal']

# Specify how to execute alarm command.
send_alarm_command = ""
''')

            os.chmod(config_file, 0o755)
        except Exception as error:
            print('*Error*: Failed on opening config file "' + str(config_file) + '" for write: ' + str(error))
            sys.exit(1)


def gen_run_web_script():
    """
    Generate web/run.sh.
    """
    run_web_script = 'web/run.sh'
    print('>>> Generate run web script "' + str(run_web_script) + '".')

    with open(run_web_script, 'w') as RWS:
        RWS.write('#!/bin/bash\n')
        RWS.write('\n')
        RWS.write('export MONITOR_VIEWER_INSTALL_PATH=' + str(CWD) + '\n')
        RWS.write('cd ${MONITOR_VIEWER_INSTALL_PATH}/web\n')
        RWS.write('flask run --host=0.0.0.0\n')

    os.chmod(run_web_script, 0o755)


################
# Main Process #
################
def main():
    check_python_version()
    gen_shell_tools()
    gen_config_file()
    gen_run_web_script()

    print('')
    print('Done, Please enjoy it.')


if __name__ == '__main__':
    main()
