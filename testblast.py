#!/usr/bin/env python

import time
import subprocess
import math

BLAST_OUT = "/dev/pi-blaster"


def blast_pin(pin, percentage):
    pwm = '{pin}={perc}'.format(pin=pin, perc=percentage / 100.0)
    cmd = 'echo "{pwm}" > {blast}'.format(pwm=pwm, blast=BLAST_OUT)
    subprocess.call(cmd, shell=True)


if __name__ == "__main__":
    i = 0
    s = 0
    while True:
        blast_pin(23, s)
        i += 0.1
        s = 50 * math.sin(i) + 50
        time.sleep(0.1)
