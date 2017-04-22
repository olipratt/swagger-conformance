"""
This file makes the tests directory a package, which is required for
``unittest discover``.

It also sets up logging so that is is enabled for all the tests when run using
``unittest discover``.
"""
import logging


# Set up debug logging to file here so it's enabled when the unit tests are
# run with `unittest descover`.
# basicConfig won't work due to UTF-8 encoding so this needs some extra steps.
LOG_FORMAT = '%(asctime)s:%(levelname)-7s:%(funcName)s:%(message)s'
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('python_ut_debug.log', 'w', 'utf-8')
handler.setFormatter(logging.Formatter(LOG_FORMAT))
root_logger.addHandler(handler)
