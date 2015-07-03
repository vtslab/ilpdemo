import re
from subprocess import Popen, PIPE


# ip6regex = r'([a-f\d]+)::([a-f\d]+):([a-f\d]+):([a-f\d]+):([a-f\d]+)'
ip4regex = r'(\d+)\.(\d+)\.(\d+)\.(\d+)'


def call_and_decode(command):
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    msg, err = p.communicate()
    return msg.decode('utf8')


def avahi_resolve(hostname, ip4=True):
    if hostname is None:
        return

    avahi_resolve = ['avahi-resolve', '-n']
    if ip4:
        avahi_resolve += ['-4']
    return call_and_decode(avahi_resolve + ['{}.local'.format(hostname)])


def get_ip(hostname, default=None):
    msg = avahi_resolve(hostname)

    # ip6match = re.search(ip6regex, msg)

    # while ip6match:
    #     msg = avahi_resolve(hostname)
    #     ip6match = re.search(ip6regex, msg)

    ip4match = re.search(ip4regex, msg)
    return ip4match.group(0) if ip4match else default


def get_hostname(own=True):
    return call_and_decode(['hostname']).strip()
