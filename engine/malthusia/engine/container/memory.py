import marshal
import logging

logger = logging.getLogger(__name__)

def get_dict_repr(d, objs=None):
    """
    Returns a dict representation of any object, using only primitive types, strings, dicts and lists.
    """
    if objs is None:
        objs = []
    for dd in objs:
        if d is dd:
            return 0 # dont need to count twice
    objs.append(d)
    if hasattr(d, "__dict__"):
        return get_dict_repr(d.__dict__, objs=objs)
    # only builtins from now on, please
    assert(type(d).__module__ == "builtins")
    if hasattr(d, "items"):
        nd = {}
        for k, v in d.items():
            nd[k] = get_dict_repr(v, objs=objs)
        return nd
    if isinstance(d, str):
        return d
    if hasattr(d, "__iter__"):
        nd = []
        for v in d:
            nd.append(get_dict_repr(v, objs=objs))
        return nd
    if type(d).__name__  == "builtin_function_or_method" or type(d).__name__.endswith("_descriptor"):
        return 1
    return d

def bytes_usage(obj):
    """
    Returns an approximation for the number of bytes used by the object.
    """
    obj_dict = get_dict_repr(obj)
    logger.debug(f"obj dict: {obj_dict}")
    # we marshal instead of pickle. this is important, because pickle is doing some amount of compression
    return len(marshal.dumps(obj_dict))