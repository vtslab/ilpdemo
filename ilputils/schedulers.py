#!/usr/bin/env python

import time
from datetime import datetime, timedelta
from threading import Thread

from .pwm import print_pin, set_pins

DEFAULT = -1
MAX_INTENSITY = 255


class LedsSchedule(object):
    def __init__(self, leds=None, start_time=None, color=DEFAULT,
                 intensity=DEFAULT):
        if isinstance(leds, (tuple, list)):
            self.leds = leds
        elif leds is None:
            self.leds = [0, 1]
        else:
            self.leds = [leds]

        assert isinstance(start_time, datetime), 'Time must be a datetime object'
        self.time = start_time

        assert DEFAULT <= color <= 0xFFFFFF, \
            'Color must be between {} and 0xFFFFFF, got {}'.format(DEFAULT,
                                                                   color)
        self.color = color
        assert DEFAULT <= intensity <= MAX_INTENSITY, \
            'Intensity must be between {} and {}, got {}'.format(DEFAULT,
                                                                 MAX_INTENSITY,
                                                                 intensity)
        self.intensity = intensity

    @property
    def settings(self):
        return {
            'color': self.color,
            'intensity': self.intensity
        }

    @property
    def array_settings(self):
        return [str(self.time), self.leds, self.color, self.intensity]


class DefaultValueSchedule(object):

    """
    Maintains a schedule of future default values.

    The schedule may change anytime so default values should not be resolved
    with get() until execution
    """

    def __init__(self, items=None):
        self._items = []
        self.items = [] if items is None else items

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        for item in items:
            assert isinstance(item, LedsSchedule), 'Only LedsSchedule allowed'
        self._items = items

    def add(self, start_datetime, color=DEFAULT, intensity=DEFAULT):
        self._items.append(LedsSchedule(start_time=start_datetime, color=color,
                                        intensity=intensity))
        self._items = sorted(
            (i for i in self._items if i.time >= datetime.utcnow()),
            key=lambda x: x.time)

    def get_color(self, time):
        for item in reversed(self._items):
            if time > item.time and item.color != DEFAULT:
                return item.color

    def get_intensity(self, time):
        for item in reversed(self._items):
            if time > item.time and item.intensity != DEFAULT:
                return item.intensity


class ILPScheduler(Thread):
    """Scheduler in a separate thread"""

    TIMEGRANULARITY = 1 / 50  # Eye detection limit; avoid 50 Hz

    def __init__(self, default_color=0xFFFFFF, default_intensity=192):
        super(ILPScheduler, self).__init__()
        self._items = []
        self._max_datetime = datetime.utcnow()
        self._default = DefaultValueSchedule()
        self._DEFAULT_COLOR = default_color
        self._DEFAULT_INTENSITY = default_intensity
        self.running = False

    def run(self):
        self.running = True
        self.add(
            LedsSchedule(start_time=datetime.utcnow() + timedelta(seconds=0.5),
                         color=self._DEFAULT_COLOR,
                         intensity=self._DEFAULT_INTENSITY))
        while self.running:
            tstart = time.time()
            self._set_changes(self._get_changed_settings())
            sleep_time = self.TIMEGRANULARITY - time.time() + tstart
            if sleep_time > 0:
                time.sleep(sleep_time)

    def get(self):
        return self._items

    def add(self, schedule, overwrite=False):
        assert isinstance(schedule, LedsSchedule)
        now = datetime.utcnow()
        if schedule.time < now or (
                schedule.time < self._max_datetime and not overwrite):
            return
        self._items.append(schedule)
        self._max_datetime = max(self._max_datetime, schedule.time)
        if schedule.color != DEFAULT and schedule.intensity != DEFAULT:
            self._default.add(schedule.time, schedule.color,
                              schedule.intensity)
        elif schedule.color != DEFAULT:
            self._default.add(schedule.time, schedule.color)
        elif schedule.intensity != DEFAULT:
            self._default.add(schedule.time, intensity=schedule.intensity)
        self._items.sort(key=lambda x: x.time)

    def _get_changed_settings(self):
        tb_executed = []
        for item in self._items:
            if item.time < datetime.utcnow():
                if item.color == DEFAULT:
                    color = self._default.get_color(item.time)
                    if color is None:
                        color = self._DEFAULT_COLOR
                    item.color = color
                if item.intensity == DEFAULT:
                    intensity = self._default.get_intensity(item.time)
                    if intensity is None:
                        intensity = self._DEFAULT_INTENSITY
                    item.intensity = intensity
                tb_executed.append(item)
                self._items.remove(item)

        settings = {}
        for item in tb_executed:
            if 0 in item.leds:
                settings['led0'] = item.settings
            if 1 in item.leds:
                settings['led1'] = item.settings
        return settings

    def _set_changes(self, settings):
        led0 = settings.get('led0')
        led1 = settings.get('led1')

        cmds = []
        if led0:
            print_pin(23, led0['intensity'] / MAX_INTENSITY)
            cmds.append([23, led0['intensity'] / MAX_INTENSITY])
        if led1:
            print_pin(24, led1['intensity'] / MAX_INTENSITY)
            cmds.append([24, led1['intensity'] / MAX_INTENSITY])

        set_pins(cmds)
