import subprocess
import json
import argparse
import sys
import ctypes

TASK_STATES_MAP = {
    0: 'Unkown',
    1: 'Disabled',
    2: 'Queued',
    3: 'Ready',
    4: 'Running'
}

class TaskNotFoundError(Exception): 
    pass
class AdministrativeRightsRequiredError(Exception): 
    pass

def powershell_command(command):
    process = subprocess.Popen(['C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe', '-Command', command],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    (stdout, stderr) = process.communicate()

    return (stdout.decode('cp1252'), stderr.decode('cp1252'))

def raise_for_non_administrative_windows_rights():
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        raise AdministrativeRightsRequiredError

def get_scheduled_task():
    (stdout, stderr) = powershell_command('Get-ScheduledTask -TaskName "Certbot Renew Task" -ErrorAction Ignore | ConvertTo-Json')

    if stderr:
        raise ValueError('''Error encountered while getting the Certbot Renew Task task: 
{0}'''.format(stderr))

    if not stdout:
        raise TaskNotFoundError()

    return json.loads(stdout)

def show_task_status():
    status = get_scheduled_task()
    print('Task name: {0}'.format(status['TaskName']))
    print('State: {0}'.format(TASK_STATES_MAP.get(status['State'])))

def create_task():
    raise_for_non_administrative_windows_rights()
    try:
        get_scheduled_task()
        print('The task Certbot Renew Task already exists.')
    except TaskNotFoundError:
        (_, stderr) = powershell_command('''
$action = New-ScheduledTaskAction -Execute 'Powershell.exe' -Argument '-NoProfile -WindowStyle Hidden -Command "certbot renew"'
$triggerAM = New-ScheduledTaskTrigger -Daily -At 12am
$triggerPM = New-ScheduledTaskTrigger -Daily -At 12pm
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType S4U -RunLevel Highest
Register-ScheduledTask -Action $action -Trigger $triggerAM,$triggerPM -TaskName "Certbot Renew Task" -Description "Execute twice a day the 'certbot renew' command, to renew Let's Encrypt certificates if needed." -Principal $principal
''')

        if stderr:
            raise ValueError('''Error encountered while creating the Certbot Renew Task task: 
{0}'''.format(stderr))

    print('The task Certbot Renew Task has been created and is enabled.')

def delete_task():
    raise_for_non_administrative_windows_rights()
    get_scheduled_task()

    (_, stderr) = powershell_command('Unregister-ScheduledTask -TaskName "Certbot Renew Task" -Confirm:$false')

    if stderr:
        raise ValueError('''Error encountered while deleting the Certbot Renew Task task: 
{0}'''.format(stderr))

    print('The task Certbot Renew Task has been deleted.')

def enable_task():
    raise_for_non_administrative_windows_rights()
    get_scheduled_task()

    (_, stderr) = powershell_command('Enable-ScheduledTask -TaskName "Certbot Renew Task"')

    if stderr:
        raise ValueError('''Error encountered while enabling the Certbot Renew Task task: 
{0}'''.format(stderr))

    print('The task Certbot Renew Task has been enabled.')

def disable_task():
    raise_for_non_administrative_windows_rights()
    get_scheduled_task()

    (_, stderr) = powershell_command('Disable-ScheduledTask -TaskName "Certbot Renew Task"')

    if stderr:
        raise ValueError('''Error encountered while disabling the Certbot Renew Task task: 
{0}'''.format(stderr))

    print('The task Certbot Renew Task has been disabled.')

def build_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Sub-commands available on the Certbot Renew Task task.')

    status = subparsers.add_parser('status', help='Show the task status.')
    status.set_defaults(function=show_task_status)
    
    create = subparsers.add_parser('create', help='Create the task and enable it.')
    create.set_defaults(function=create_task)
    
    delete = subparsers.add_parser('delete', help='Delete the task.')
    delete.set_defaults(function=delete_task)

    enable = subparsers.add_parser('enable', help='Enable the task.')
    enable.set_defaults(function=enable_task)


    disable = subparsers.add_parser('disable', help='Disable the task without deleting it.')
    disable.set_defaults(function=disable_task)

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.function:
        try:
            args.function()
        except TaskNotFoundError:
            print('Task Certbot Renew Task does not exist.\nPlease create it using the following command: \'certbot-scheduler create\'.')
            sys.exit(1)
        except AdministrativeRightsRequiredError:
            print('Error, subcommand must be run on a shell with administrative rights.')
            sys.exit(1)

if __name__ == '__main__':
    main()
