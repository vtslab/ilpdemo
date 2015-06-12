import subprocess


BLAST_OUT = "/dev/pi-blaster"


def format_set_pin(pin, dutycycle):
    p = 0. if dutycycle < 0 else dutycycle if dutycycle < 1 else 1.
    pwm = '{pin}={dutycycle}'.format(pin=pin, dutycycle=p)
    return 'echo "{pwm}" > {blast}'.format(pwm=pwm, blast=BLAST_OUT)


def set_pin(pin=23, dutycycle=0.2):
    subprocess.call(format_set_pin(pin, dutycycle), shell=True)


def print_pin(pin=23, dutycycle=0.23):
    print(format_set_pin(pin, dutycycle))


def set_pins(config):
    cmds = ' && '.join([format_set_pin(p, d) for p, d in config])
    subprocess.call(cmds, shell=True)
