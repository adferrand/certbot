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

class TaskNotFoundError(Exception): pass
class AdministrativeRightsRequiredError(Exception): pass

def powershell_command(command):
    p = subprocess.Popen(['C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe', '-Command', command],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()

    return (stdout.decode('cp1252'), stderr.decode('cp1252'))

def raise_for_non_administrative_windows_rights():
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        raise AdministrativeRightsRequiredError

def get_scheduled_task():
    (stdout, stderr) = powershell_command('Get-ScheduledTask -TaskName "CertbotRenew" -ErrorAction Ignore | ConvertTo-Json')

    if stderr:
        raise ValueError('''Error encountered while getting the CertbotRenew task: 
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
        status = get_scheduled_task()
        print('The task CertbotRenew already exists.')
    except TaskNotFoundError:
        (_, stderr) = powershell_command('''
$action = New-ScheduledTaskAction -Execute 'certbot' -Argument 'renew'
$trigger1 = New-ScheduledTaskTrigger -Daily -At 12pm
$trigger2 = New-ScheduledTaskTrigger -Daily -At 12am
Register-ScheduledTask -Action $action -Trigger $trigger1,$trigger2 -TaskName "CertbotRenew" -Description "Excute twice a day the certbot renew command"
''')

        if stderr:
            raise ValueError('''Error encountered while creating the CertbotRenew task: 
{0}'''.format(stderr))

    print('The task CertbotRenew has been created and is enabled.')

def delete_task():
    raise_for_non_administrative_windows_rights()
    get_scheduled_task()

    (_, stderr) = powershell_command('Unregister-ScheduledTask -TaskName "CertbotRenew" -Confirm:$false')

    if stderr:
        raise ValueError('''Error encountered while deleting the CertbotRenew task: 
{0}'''.format(stderr))

    print('The task CertbotRenew has been deleted.')

def enable_task():
    raise_for_non_administrative_windows_rights()
    get_scheduled_task()

    (_, stderr) = powershell_command('Enable-ScheduledTask -TaskName "CertbotRenew"')

    if stderr:
        raise ValueError('''Error encountered while enabling the CertbotRenew task: 
{0}'''.format(stderr))

    print('The task CertbotRenew has been enabled.')

def disable_task():
    raise_for_non_administrative_windows_rights()
    get_scheduled_task()

    (_, stderr) = powershell_command('Disable-ScheduledTask -TaskName "CertbotRenew"')

    if stderr:
        raise ValueError('''Error encountered while disabling the CertbotRenew task: 
{0}'''.format(stderr))

    print('The task CertbotRenew has been disabled.')

def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument
    subparsers = parser.add_subparsers(help='Sub-commands available on the CertbotRenew task.')

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

if __name__ == '__main__':
    parser = build_parser()
    args = parser.parse_args()

    if args.function:
        try:
            args.function()
        except TaskNotFoundError:
            print('Task CertbotRenew does not exist.\nPlease create it using the following command: \'certbot-scheduler create\'.')
            sys.exit(1)
        except AdministrativeRightsRequiredError:
            print('Error, subcommand must be run on a shell with administrative rights.')
            sys.exit(1)
