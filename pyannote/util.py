import warnings
from decorator import decorator

def deprecated(replacedByFunc):
    def _d(f, *args, **kwargs):
        warnings.warn('"%s" is deprecated. use "%s" instead.' % (f.func_name, replacedByFunc.__name__))
        return f(*args, **kwargs)
    return decorator(_d)

    