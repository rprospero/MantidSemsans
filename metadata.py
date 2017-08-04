#!/usr/bin/python
import re
import datetime
import os.path
import xml.etree
from mantid.simpleapi import CreateEmptyTableWorkspace, RenameWorkspace
from .runtypes import HeData, RunData, QuickData


def numbered_run(x):
    return re.match(r'(.+) run: (\d+)_SANS', x) or \
        re.match(r'MT Beam_SANS', x) or \
        re.match(r'D2. 2mm_SANS', x)


def trans_run(x):
    return re.match(r".+_TRANS", x)


def can_sans(x):
    return re.match(r"D2. 2mm_SANS", x)


def can_trans(x):
    return re.match(r"D2. 2mm_TRANS", x)


def direct_trans(x):
    return re.match(r"MT Beam_TRANS", x)


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


def convert_run(run, trans, csans, ctrans, dtrans, hetemp):
    if re.match(r'(.+) run: (\d+)_SANS', run.sample):
        sample = re.match(r'(.+) run: (\d+)_SANS', run.sample).group(1)
    else:
        sample = "Full Blank"
    duration = run[3]

    he_run = hetemp[0]
    for he3 in hetemp[1:]:
        if he3.dt < run.start:
            he_run = he3
        else:
            break

    scale = he_run.scale
    pump = he_run.dt
    lifetime = he_run.t1 * 3600
    decay_time = (run.start - pump).seconds / lifetime
    decay_time2 = (run.start - pump + duration).seconds / lifetime

    tr = -1
    for tran in trans:
        if sample in tran[1]:
            tr = tran[0]
    csans.sort(key=lambda x: x[2]-run.start)
    ctrans.sort(key=lambda x: x[2]-run.start)
    dtrans.sort(key=lambda x: x[2]-run.start)
    return RunData(run.number, sample, scale, decay_time, decay_time2, tr,
                   int(csans[0][0]), int(ctrans[0][0]),
                   int(dtrans[0][0]), run.start.isoformat())


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


def get_log(runs):
    hetemp = load_helium_file(
        os.path.join(
            r"C:\Users\auv61894\Dropbox\Science\Edler\Edler_May_2017",
            "heruns.tsv"))

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
                        elif "duration" in param.tag:
                            duration = datetime.timedelta(
                                seconds=int(param.text))
                        elif "proton_charge" in param.tag:
                            proton_charge = float(param.text)
                    results.append(
                        QuickData(num, sample, start, duration, proton_charge))
                child.clear()
                if num > max(runs):
                    break
    trans = [run for run in results
             if trans_run(run[1])]
    csans = [run for run in results
             if can_sans(run[1])]
    ctrans = [run for run in results
              if can_trans(run[1])]
    dtrans = [run for run in results
              if direct_trans(run[1])]
    temp = [convert_run(run, trans, csans, ctrans, dtrans, hetemp)
            for run in results
            if numbered_run(run.sample) and run.charge > 8]

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
        my_table.addColumn("float", "Scale")
        my_table.addColumn("float", "He3 Start")
        my_table.addColumn("float", "He3 End")
        my_table.addColumn("int", "Trans run")
        my_table.addColumn("int", "Can Sans run")
        my_table.addColumn("int", "Can Trans run")
        my_table.addColumn("int", "Direct Trans run")
        my_table.addColumn("str", "Start time")

        for run in v:
            my_table.addRow(run)
        RenameWorkspace(my_table, k+"_runs")
