from collections import namedtuple

HeData = namedtuple("HeData", "run cell scale dt fid t1")
RunData = namedtuple("RunData", "number sample scale start end "
                     "trans csans ctrans direct time")
QuickData = namedtuple("QuickData", "number sample start duration charge")
