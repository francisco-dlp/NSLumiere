import logging
try:
    from . import ClassPatch
except ImportError:
    logging.info(f"***ClassPatch***: Problem patching one or more classes. Please dig more by removing this excetion handler.")