#!/usr/bin/python
import re
import datetime
import xml.etree
from mantid.simpleapi import CreateEmptyTableWorkspace, RenameWorkspace, mtd
from .runtypes import HeData, RunData, QuickData

RUN_IDENTIFIERS = {
    "run": r'(.+) run: (\d+)_SANS',
    "trans": r".+_TRANS",
    "can_sans": r"D2. 2mm_SANS",
    "can_trans": r"D2. 2mm_TRANS",
    "direct_sans": "MT Beam_SANS",
    "direct_trans": "MT Beam_TRANS"}


def convert_he(i):
    run = int(i[0])
    cell = i[1]
    pl = float(i[2])
    phe = float(i[3]) / 100.0
    dt = datetime.datetime.strptime(i[4] + " " + i[5], "%m/%d/%Y %H:%M")
    fid = float(i[6])
    t1 = float(i[7])

    return HeData(run, cell, 0.0733 * pl * phe, dt, fid, t1)


def load_helium_file(f):
    with open(f, "r") as infile:
        infile.readline()  # read header
        return [convert_he(line.split("\t"))
                for line in infile]


def convert_run(run, trans, csans, ctrans, dtrans):
    if re.match(r'(.+) run: (\d+)_SANS', run.sample):
        sample = re.match(r'(.+) run: (\d+)_SANS', run.sample).group(1)
    else:
        sample = "Full Blank"
    duration = run[3]

    tr = -1
    for tran in trans:
        if sample in tran[1]:
            tr = tran[0]
    csans.sort(key=lambda x: x[2]-run.start)
    ctrans.sort(key=lambda x: x[2]-run.start)
    dtrans.sort(key=lambda x: x[2]-run.start)
    return RunData(run.number, sample, run.start, run.end, tr,
                   int(csans[0][0]), int(ctrans[0][0]),
                   int(dtrans[0][0]))


JPATH = r'\\isis\inst$\NDXLARMOR\Instrument\logs\journal'


def get_relevant_log(run):
    with open(JPATH+r"\journal_main.xml", "r") as infile:
        journals = xml.etree.ElementTree.parse(infile)
    for child in journals.getroot():
        if int(child.attrib["first_run"]) <= run and \
           run <= int(child.attrib["last_run"]):
            return child.attrib["name"]


def get_xml_run_number(node):
    for child in node:
        if "run_number" in child.tag:
            return int(child.text)


def get_he3_log(path):
    hetemp = load_helium_file(path)
    my_table = CreateEmptyTableWorkspace()
    my_table.addColumn("int", "Number")
    my_table.addColumn("str", "Cell")
    my_table.addColumn("float", "scale")
    my_table.addColumn("str", "Start time")
    my_table.addColumn("float", "fid")
    my_table.addColumn("float", "Time Constant")

    for run in hetemp:
        my_table.addRow([run.run, run.cell,
                         run.scale,
                         run.dt.isoformat(),
                         run.fid, run.t1])
    RenameWorkspace(my_table, "helium_log")


def get_log(runs):
    log_file = JPATH + "\\" + get_relevant_log(min(runs))
    results = []
    with open(log_file, "r") as infile:
        journal = xml.etree.cElementTree.iterparse(infile)
        for _, child in journal:
            if "NXentry" in child.tag:
                num = get_xml_run_number(child)
                if num in runs:
                    for param in child:
                        if "title" in param.tag:
                            sample = param.text
                        elif "start_time" in param.tag:
                            start = datetime.datetime.strptime(
                                param.text,
                                "%Y-%m-%dT%H:%M:%S")
                        elif "end_time" in param.tag:
                            stop = datetime.datetime.strptime(
                                param.text,
                                "%Y-%m-%dT%H:%M:%S")
                        elif "duration" in param.tag:
                            duration = datetime.timedelta(
                                seconds=int(param.text))
                        elif "proton_charge" in param.tag:
                            proton_charge = float(param.text)
                    results.append(
                        QuickData(num, sample, start, stop, duration, proton_charge))
                child.clear()
                if num > max(runs):
                    break
    trans = [run for run in results
             if re.match(RUN_IDENTIFIERS["trans"], run[1])]
    csans = [run for run in results
             if re.match(RUN_IDENTIFIERS["can_sans"], run[1])]
    ctrans = [run for run in results
              if re.match(RUN_IDENTIFIERS["can_trans"], run[1])]
    dtrans = [run for run in results
              if re.match(RUN_IDENTIFIERS["direct_trans"], run[1])]
    temp = [convert_run(run, trans, csans, ctrans, dtrans)
            for run in results
            if (re.match(RUN_IDENTIFIERS["run"], run.sample) or
                re.match(RUN_IDENTIFIERS["can_sans"], run.sample) or
                re.match(RUN_IDENTIFIERS["direct_sans"], run.sample))
            and run.charge > 8]

    d = {}
    for run in temp:
        if run.sample in d.keys():
            d[run.sample].append(run)
        else:
            d[run.sample] = [run]

    for k, v in d.items():
        my_table = CreateEmptyTableWorkspace()
        my_table.addColumn("int", "Run Number")
        my_table.addColumn("str", "Sample")
        my_table.addColumn("str", "Start time")
        my_table.addColumn("str", "End time")
        my_table.addColumn("int", "Trans run")
        my_table.addColumn("int", "Can Sans run")
        my_table.addColumn("int", "Can Trans run")
        my_table.addColumn("int", "Direct Trans run")

        for run in v:
            my_table.addRow(
                [run.number, run.sample,
                 run.start.isoformat(),
                 run.end.isoformat(),
                 run.trans, run.csans, run.ctrans,
                 run.direct])
        RenameWorkspace(my_table, k+"_runs")
