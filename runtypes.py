import datetime
from collections import namedtuple

HeData = namedtuple("HeData", "run cell scale dt fid t1")
RunData = namedtuple("RunData", "number sample scale start end "
                     "trans csans ctrans direct time")
QuickData = namedtuple("QuickData", "number sample start duration charge")

def table_to_run(table):
    return [
        RunData(x["Run Number"], x["Sample"], x["Scale"], x["He3 Start"],
                x["He3 End"], x["Trans run"], x["Can Sans run"],
                x["Can Trans run"], x["Direct Trans run"],
                datetime.datetime.strptime(x["Start time"],
                                           "%Y-%m-%dT%H:%M:%S"))
        for x in table]
