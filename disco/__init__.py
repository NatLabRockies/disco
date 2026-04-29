"""DISCO package"""

import logging
from jade.utils.timing_utils import TimerStatsCollector

logging.getLogger(__name__).addHandler(logging.NullHandler())
timer_stats_collector = TimerStatsCollector()

# EV hosting capacity API
from disco.ev import EVHostingCapacity, EVHostingCapacityResults, Feeder