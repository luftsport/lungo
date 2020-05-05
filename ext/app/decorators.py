"""
	Decorators without response
	===========================

	NO response object should be used or

"""
from functools import wraps
from threading import Thread, Timer
from datetime import datetime
from inspect import signature
import time


def async(f):
    """ An async decorator
    Will spawn a seperate thread executing whatever call you have
    """

    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()

    return wrapper


def track_time_spent(name):
    """Time something
    """

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            start = datetime.now()
            delta = datetime.now() - start
            print(name, "took", delta.total_seconds(), "seconds")
            return f(*args, **kwargs)

        return wrapped

    return decorator


def throttle(wait, keep=60, hash=False):
    """Decorator ensures function that can only be called once every `s` seconds.
    wait seconds to supress call
    keep seconds to keep call in memory
    """

    def decorate(f):

        sig = signature(f)
        caller = {}

        def wrapped(*args, **kwargs):
            nonlocal caller

            try:
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                called_args = f.__name__ + str(dict(bound_args.arguments))
            except:
                called_args = ''

            t_ = time.time()

            if caller.get(called_args, None) is None or t_ - caller.get(called_args, 0) >= wait:
                result = f(*args, **kwargs)

                caller = {key: val for key, val in caller.items() if t_ - val > keep}
                caller[called_args] = t_
                return result

            caller = {key: val for key, val in caller.items() if t_ - val > keep}
            caller[called_args] = t_

        return wrapped

    return decorate


def debounce(wait):
    def decorator(fn):
        sig = signature(fn)
        caller = {}

        def debounced(*args, **kwargs):
            nonlocal caller

            try:
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                called_args = fn.__name__ + str(dict(bound_args.arguments))
            except:
                called_args = ''

            t_ = time.time()

            def call_it(key):
                try:
                    # always remove on call
                    caller.pop(key)
                except:
                    pass

                fn(*args, **kwargs)

            try:
                # Always try to cancel timer
                caller[called_args].cancel()
            except:
                pass

            caller[called_args] = Timer(wait, call_it, [called_args])
            caller[called_args].start()

        return debounced

    return decorator
