# from keras.utils.generic_utils import Progbar

import sys
import collections
import time
import numpy as np

def clip_read():
    from pandas.io import clipboard
    clipboard.clipboard_get()
def clip_write(x):
    from pandas.io import clipboard
    clipboard.clipboard_set(x)

def chunker(seq, size, progbar=True):
    "Use this as: for batch in chunker(mylist, 1000): ..."
    # from http://stackoverflow.com/a/434328
    n = len(seq)
    if progbar:
        pbar: Progbar = Progbar(n)
        pbar.update(0)
    for pos in range(0, n, size):
        yield seq[pos:pos + size]
        if progbar:
            pbar.update(min(pos+size,n))
def insert_with_progbar(engine, df, name, if_exists='replace', chunksize=1000, **kwargs):
    # from https://stackoverflow.com/questions/39494056/progress-bar-for-pandas-dataframe-to-sql
    pbar = Progbar(len(df))
    for i, cdf in enumerate(chunker(df, chunksize)):
        replace = if_exists if i == 0 else "append"
        cdf.to_sql(name=name, con=engine, if_exists=replace, **kwargs)
        pbar.add(chunksize)

# Source?
class Progbar(object):
    """Displays a progress bar.

    # Arguments
        target: Total number of steps expected, None if unknown.
        width: Progress bar width on screen.
        verbose: Verbosity mode, 0 (silent), 1 (verbose), 2 (semi-verbose)
        stateful_metrics: Iterable of string names of metrics that
            should *not* be averaged over time. Metrics in this list
            will be displayed as-is. All others will be averaged
            by the progbar before display.
        interval: Minimum visual progress update interval (in seconds).
    """

    def __init__(self, target, width=30, verbose=1, interval=0.05,
                 stateful_metrics=None):
        self.target = target
        self.width = width
        self.verbose = verbose
        self.interval = interval
        if stateful_metrics:
            self.stateful_metrics = set(stateful_metrics)
        else:
            self.stateful_metrics = set()

        self._dynamic_display = ((hasattr(sys.stdout, 'isatty') and
                                  sys.stdout.isatty()) or
                                 'ipykernel' in sys.modules)
        self._total_width = 0
        self._seen_so_far = 0
        self._values = collections.OrderedDict()
        self._start = time.time()
        self._last_update = 0

    def update(self, current, values=None):
        """Updates the progress bar.

        # Arguments
            current: Index of current step.
            values: List of tuples:
                `(name, value_for_last_step)`.
                If `name` is in `stateful_metrics`,
                `value_for_last_step` will be displayed as-is.
                Else, an average of the metric over time will be displayed.
        """
        values = values or []
        for k, v in values:
            if k not in self.stateful_metrics:
                if k not in self._values:
                    self._values[k] = [v * (current - self._seen_so_far),
                                       current - self._seen_so_far]
                else:
                    self._values[k][0] += v * (current - self._seen_so_far)
                    self._values[k][1] += (current - self._seen_so_far)
            else:
                # Stateful metrics output a numeric value.  This representation
                # means "take an average from a single value" but keeps the
                # numeric formatting.
                self._values[k] = [v, 1]
        self._seen_so_far = current

        now = time.time()
        # info = ' - %.0fs' % (now - self._start)
        info = ' - %s' % (formatTime(now - self._start))
        if self.verbose == 1:
            if (now - self._last_update < self.interval and
                    self.target is not None and current < self.target):
                return

            prev_total_width = self._total_width
            if self._dynamic_display:
                sys.stdout.write('\b' * prev_total_width)
                sys.stdout.write('\r')
            else:
                sys.stdout.write('\n')

            if self.target is not None and self.target>0:
                try:
                    numdigits = int(np.floor(np.log10(self.target))) + 1
                except:
                    numdigits=1
                barstr = '%%%dd/%d [' % (numdigits, self.target)
                bar = barstr % current
                prog = float(current) / self.target
                prog_width = int(self.width * prog)
                if prog_width > 0:
                    bar += ('=' * (prog_width - 1))
                    if current < self.target:
                        bar += '>'
                    else:
                        bar += '='
                bar += ('.' * (self.width - prog_width))
                bar += ']'
            else:
                bar = '%7d/Unknown' % current

            self._total_width = len(bar)
            sys.stdout.write(bar)

            if current:
                time_per_unit = (now - self._start) / current
            else:
                time_per_unit = 0
            if self.target is not None and current < self.target:
                eta = time_per_unit * (self.target - current)
                eta_format = formatTime(eta)

                info = ' - ETA: %s' % eta_format
            else:
                if time_per_unit >= 1:
                    info += ' %.0fs/step' % time_per_unit
                elif time_per_unit >= 1e-3:
                    info += ' %.0fms/step' % (time_per_unit * 1e3)
                else:
                    info += ' %.0fus/step' % (time_per_unit * 1e6)

            for k in self._values:
                info += ' - %s:' % k
                if isinstance(self._values[k], list):
                    avg = np.mean(
                        self._values[k][0] / max(1, self._values[k][1]))
                    if abs(avg) > 1e-3:
                        info += ' %.4f' % avg
                    else:
                        info += ' %.4e' % avg
                else:
                    info += ' %s' % self._values[k]

            self._total_width += len(info)
            if prev_total_width > self._total_width:
                info += (' ' * (prev_total_width - self._total_width))

            if self.target is not None and current >= self.target:
                info += '\n'

            sys.stdout.write(info)
            sys.stdout.flush()

        elif self.verbose == 2:
            if self.target is None or current >= self.target:
                for k in self._values:
                    info += ' - %s:' % k
                    avg = np.mean(
                        self._values[k][0] / max(1, self._values[k][1]))
                    if avg > 1e-3:
                        info += ' %.4f' % avg
                    else:
                        info += ' %.4e' % avg
                info += '\n'

                sys.stdout.write(info)
                sys.stdout.flush()

        self._last_update = now

    def add(self, n, values=None):
        self.update(self._seen_so_far + n, values)

def formatTime(eta):
    if eta > 3600:
        eta_format = ('%d:%02d:%02d' %
                    (eta // 3600, (eta % 3600) // 60, eta % 60))
    elif eta > 60:
        eta_format = '%d:%02d' % (eta // 60, eta % 60)
    else:
        eta_format = '%ds' % eta
    return eta_format

def formatTime_ns(eta):
    if eta > 10e9:
        eta_format = formatTime(eta//1e9)
    elif eta > 1e9:
        eta_format = '%.1fs' % (eta/1e9)
    elif eta > 10e6:
        eta_format = '%dms' % (eta / 1e6)
    elif eta > 1e6:
        eta_format = '%.1fms' % (eta / 1e6)
    else:
        eta_format = '%.1fus' % (eta / 1e3)
    return eta_format


if 'time_ns' in dir(time):
    def _time_ns():
        return time.time_ns()
else:
    def _time_ns():
        return int(time.time() * 1e9)


class Tictoc(object):
    def __init__(self, output='print', additive=False):
        self.stack = []
        self.output = output
        from collections import defaultdict
        self._summarizer = defaultdict(int) if additive else False
        self._prefix = None
    def tic(self, name):
        if self._summarizer != False:
            self._summarizer[name]
        self.stack.append( (name, _time_ns()) )
    def toc(self):
        stop = _time_ns()
        name, start = self.stack.pop()
        dur = stop - start
        if self.output == 'print':
            timeString = formatTime_ns(dur)
            print(f"{name}: {timeString}")
        if self._summarizer != False:
            self._summarizer[name] += dur
    def clear(self):
        self.stack = []
    def wrap(self, iter, name):
        self.tic(name)
        for i in iter:
            self.toc()
            yield i
            self.tic(name)
        self.toc()
    def summary(self):
        if len(self.stack):
            print(f"Warning: stack is not empty but has {len(self.stack)} items")
        for k,v in self._summarizer.items():
            print(f"{k}: {formatTime_ns(v)}")

def rmNanFromDict(x):
    import pandas as pd
    if isinstance(x, dict):
        y = {}
        for k,v in x.items():
            if isinstance(v, list) or isinstance(v, dict):
                y[k] = rmNanFromDict(v)
            elif not pd.isna(v):
                y[k] = v
        return y
    if isinstance(x, list):
        y = []
        for v in x:
            if isinstance(v, list) or isinstance(v, dict):
                y.append(rmNanFromDict(v))
            elif not pd.isna(v):
                y.append(v)
        return y
    raise Exception("x has to be a list or a dict")

def _display_and_is_jupyter():
    try:
        from IPython import display, get_ipython
        if not get_ipython():
            raise ImportError()
        return (display.display, get_ipython().has_trait('kernel'))
    except ImportError:
        return (print, False)
print_or_display, IS_JUPYTER = _display_and_is_jupyter()
