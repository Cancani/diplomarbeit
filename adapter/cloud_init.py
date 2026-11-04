"""Cloud-init für den gemeinsamen HTTP-Testdienst und den SSH-Benutzer."""
import yaml


def cloud_init(name, vm):
    cloud_config = {
        'hostname': name, 'manage_etc_hosts': True, 'disable_root': True, 'ssh_pwauth': False,
        'package_update': False, 'package_upgrade': False,
        'users': [{'name': vm['ssh']['username'], 'groups': ['sudo'], 'sudo': 'ALL=(ALL) NOPASSWD:ALL',
                   'shell': '/bin/bash', 'lock_passwd': True, 'ssh_authorized_keys': vm['ssh']['publicKeys']}],
        'write_files': [
            {'path': '/var/www/index.html', 'permissions': '0644',
             'content': vm['testService']['expectedBody'] + '\n'},
            {'path': '/etc/systemd/system/testdienst.service', 'permissions': '0644', 'content':
             '[Unit]\nDescription=HTTP-Testdienst der Lernumgebung\nAfter=network.target\n'
             '[Service]\nUser=nobody\nGroup=nogroup\nWorkingDirectory=/var/www\n'
             'ExecStart=/usr/bin/python3 -m http.server 8080 --bind 0.0.0.0 --directory /var/www\n'
             'Restart=on-failure\n[Install]\nWantedBy=multi-user.target\n'},
        ],
        'runcmd': [['systemctl', 'daemon-reload'], ['systemctl', 'enable', '--now', 'testdienst.service']],
    }
    return '#cloud-config\n' + yaml.safe_dump(cloud_config, allow_unicode=True)
