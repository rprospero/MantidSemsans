#!/usr/bin/python
import re
import datetime
import json
from .runtypes import HeData, RunData

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
        header = infile.readline()
        return [convert_he(line.split("\t"))
                for line in infile]


def convert_run(i, trans, csans, ctrans, dtrans):
    hetemp = load_helium_file("heruns.tsv")
    number = int(i[0])
    if re.match(r'(.+) run: (\d+)_SANS', i[1]):
        sample = re.match(r'(.+) run: (\d+)_SANS', i[1]).group(1)
    else:
        sample = "Full Blank"
    dt = datetime.datetime.strptime(i[2], "%a %b %d %H:%M:%S %Y")

    minutes = int(i[3].split()[0][:-1])
    seconds = int(i[3].split()[1][:-1])
    duration = datetime.timedelta(seconds=seconds, minutes=minutes)
    microamps = i[4]
    user = i[5]

    he_run = hetemp[0]
    for he3 in hetemp[1:]:
        if he3.dt < dt:
            he_run = he3
        else:
            break

    scale = he_run.scale
    pump = he_run.dt
    lifetime = he_run.t1 * 3600
    decay_time = (dt - pump).seconds / lifetime
    decay_time2 = (dt - pump + duration).seconds / lifetime

    tr = -1
    for tran in trans:
        if sample in tran:
            tr = int(tran.split("\t")[0])
    csans.sort(key=lambda x: abs(datetime.datetime.strptime(x.split("\t")[2], "%a %b %d %H:%M:%S %Y")-dt))
    ctrans.sort(key=lambda x: abs(datetime.datetime.strptime(x.split("\t")[2], "%a %b %d %H:%M:%S %Y")-dt))
    dtrans.sort(key=lambda x: abs(datetime.datetime.strptime(x.split("\t")[2], "%a %b %d %H:%M:%S %Y")-dt))
    return RunData(number, sample, scale, decay_time, decay_time2, tr,
                   int(csans[0].split("\t")[0]), int(ctrans[0].split("\t")[0]),
                   int(dtrans[0].split("\t")[0]), dt.isoformat())


def load_runs(infile, outfile):
    with open(infile, "r") as file_handle:
        lines = file_handle.readlines()
    trans = [line for line in lines
             if trans_run(line.split("\t")[1])]
    csans = [line for line in lines
             if can_sans(line.split("\t")[1])]
    ctrans = [line for line in lines
              if can_trans(line.split("\t")[1])]
    dtrans = [line for line in lines
              if direct_trans(line.split("\t")[1])]
    with open(infile, "r") as lines:
        temp = [convert_run(line.split("\t"), trans,
                            csans, ctrans, dtrans)
                for line in lines
                if numbered_run(line.split("\t")[1]) and
                float(line.split("\t")[4]) >= 8]

    d = {}
    for run in temp:
        if run.sample in d.keys():
            d[run.sample].append(run)
        else:
            d[run.sample] = [run]

    with open(outfile, "w") as outfile:
        # outfile.write(repr(d))
        json.dump(d, outfile)


#load_runs("runs.tsv", "rundict2.dat")
