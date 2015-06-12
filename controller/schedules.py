from datetime import timedelta
from ilputils.schedulers import LedsSchedule

DEFAULT = -1
MAX_INTENSITY = 255


class BaseSchedule(object):
    """Very simple interface for Schedule classes"""

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

    def add(self, leds=None, start_time=None, color=DEFAULT,
            intensity=DEFAULT):
        item = LedsSchedule(leds, start_time, color, intensity)
        self.items.append(item)


class SimpleSchedule(BaseSchedule):
    """Accepts externally defined lighting scenario"""
    def __init__(self, items=None):
        super(SimpleSchedule, self).__init__(items)


class AlarmSchedule(BaseSchedule):
    """Have both LED arrays flash a number of times synchronously"""
    def __init__(self, start_datetime, color, high_intensity, low_intensity,
                 flash_duration, flash_period, n_flashes):
        items = []
        delta = start_datetime
        for i in range(n_flashes):
            items.extend([
                LedsSchedule(start_time=delta, color=color,
                             intensity=high_intensity),
                LedsSchedule(start_time=delta + timedelta(
                    seconds=flash_duration), color=color,
                    intensity=low_intensity)])
            delta += timedelta(seconds=flash_period)
        items.append(LedsSchedule(start_time=delta))
        super(AlarmSchedule, self).__init__(items)
