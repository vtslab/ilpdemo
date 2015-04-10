# Specification of a scheduler for Intelligent Lamp Post LED arrays
# Use as pseudocode (e.g. for an implementation in C++)

# Marc de Lignie, April 10th 2015


import sys, time
from threading import Thread
from datetime import datetime, timedelta
from pprint import PrettyPrinter

DEFAULT = -1


class BaseSchedule(object):
    # Very simple interface for Schedule classes
    
    def __init__(self):
        self._items = []
    
    def getData(self):
        return self._items
    
    
class SimpleSchedule(BaseSchedule):
    # Accepts externally defined lighting scenario
    # Assumes LEDS within an array are not individually scheduled

    def __init__(self, items):
        BaseSchedule.__init__(self)
        try:
            for item in items:
                # Parse input values
                assert item['leds'] in ([0], [1], [0,1])
                assert type(item['time']).__name__ == 'datetime'
                assert item['color'] >= DEFAULT
                assert item['color'] <= 0xffffff
                assert item['intensity'] >= DEFAULT
                assert item['intensity'] <= 255
            self._items = items
        except:
            print "SimpleSchedule: Parsing error in passed items"
    

class AlarmSchedule(BaseSchedule):
    # Have both LED arrays flash a number of times synchronously
    # Assumes LEDS within an array are not individually scheduled
    
    def __init__(self, startdatetime, color, high_intensity, low_intensity, 
                                        flashduration, flashperiod, nflash):
        BaseSchedule.__init__(self)
        for i in xrange(nflash):
            self._items.append({
                'leds': [0,1],
                'time': startdatetime + timedelta(seconds = i * flashperiod),
                'color': color,
                'intensity': high_intensity
                })
            self._items.append({
                'leds': [0,1],
                'time': startdatetime + timedelta(seconds = flashduration +
                                                            i * flashperiod),
                'color': color,
                'intensity': low_intensity
                })
        self._items.append({
            'leds': [0,1],
            'time': startdatetime + timedelta(seconds = nflash * flashperiod),
            'color': DEFAULT, # Pre schedule value
            'intensity': DEFAULT
            })
            

class DefaultValueSchedule(object):
    # Maintains a schedule of future default values
    # The schedule may change anytime so default values should not be resolved
    # with get() until execution.
    
    def __init__(self):
        self._valueschedule = []
        
    def add(self, value, starttime):
        self._valueschedule.append({'starttime': starttime, 'value': value})
        for item in self._valueschedule:
            if item['starttime'] < datetime.now():
                del item        
        self._valueschedule.sort(key = lambda x: x['starttime'])
    
    def get(self, time):
        # Return the latest possible value <= time
        for i in xrange(len(self._valueschedule) -1 , -1, -1):
            if time > self._valueschedule[i]['starttime']:
                return self._valueschedule[i]['value']
                

class ILPscheduler(Thread):
    # Assumes time synchronization of ILPs to the same NTP server

    TIMEGRANULARITY = 0.017  # Eye detection limit; avoid 50 Hz
    DEFAULTCOLOR = 0xffffff  # Class variable (for all ILP arrays)
    DEFAULTINTENSITY = 192

    def __init__(self):
        Thread.__init__(self)
        self._items = []
        self._maxdatetime = datetime.now() # max explicitly scheduled time
        self._defaultcolor = DefaultValueSchedule()
        self._defaultintensity = DefaultValueSchedule()
        
    def run(self):
        self.add(SimpleSchedule([{
            'leds': [0,1],
            'time': datetime.now() + timedelta(seconds = 0.5),
#                                     min(self.TIMEGRANULARITY/1.1, 0.01)),
            'color': self.DEFAULTCOLOR,
            'intensity': self.DEFAULTINTENSITY
            }]))
        while True:    # Should run until shutdown
            tstart = time.time()
            self._setChanges(self._getChangedSettings())
            time.sleep(self.TIMEGRANULARITY - time.time() + tstart)
            
    def get(self):
        # May be used for calculating new adds or overwrites
        return self._items
                        
    def add(self, schedule, overwrite=False):
        items = sorted(schedule.getData(), key = lambda x: x['time'])
        now = datetime.now()
        for item in items:
            if item['time'] < now:  
                continue     # Skip outdated items
            if item['time'] < self._maxdatetime and not overwrite:
                continue     # Skip colliding items unless overwrite
            self._items.append(item)
            self._maxdatetime = max(self._maxdatetime, item['time'])
        if items[-1]['color'] != DEFAULT: # Implies new default
            self._defaultcolor.add(items[-1]['color'], items[-1]['time'])
        if items[-1]['intensity'] != DEFAULT:
            self._defaultintensity.add(items[-1]['intensity'],items[-1]['time'])
        self._items.sort(key = lambda x: x['time'])
        # pp = PrettyPrinter(indent=2)
        # pp.pprint(self._items)
                        
    def _getChangedSettings(self):
        tbexecuted = []
        for item in self._items:  
            if item['time'] < datetime.now():
                if item['color'] == DEFAULT:
                    item['color'] = self._defaultcolor.get(item['time'])
                if item['intensity'] == DEFAULT:
                    item['intensity'] = self._defaultintensity.get(item['time']) 
                tbexecuted.append(item)
                self._items.remove(item)
        settings = {}
        for item in tbexecuted:    # Multiple items possible in one period
            if 0 in item['leds']:  # Most recent item per array wins
                settings['led0'] = {'color': item['color'],
                                    'intensity': item['intensity']} 
            if 1 in item['leds']:
                settings['led1'] = {'color': item['color'],
                                    'intensity': item['intensity']} 
        return settings
    
    def _setChanges(self, settings):
        # serial interface to LED arrays
        for s in settings:
            pass # For python testing
            # raise(NotImplementedError)
        if len(settings) > 0:
            pp = PrettyPrinter(indent=2)
            pp.pprint(settings)
            
        
if __name__ == "__main__":
    # Usage example
    now = datetime.now()
    s1 = SimpleSchedule([{
            'leds': [0,1],
            'time': now + timedelta(seconds = 5),
            'color': 0x66ee33,
            'intensity': 20
        }])
    s2 = AlarmSchedule(now + timedelta(seconds = 10), 
                       0x2277bb, 220, 40, 0.1, 1, 3)
    ilp1 = ILPscheduler()
    ilp1.start()
    ilp1.add(s1)
    ilp1.add(s2)
#    ilp2 = ILPscheduler()
#    ilp2.start()
#    ilp2.add(s2)
#    ilp2.add(s1)

