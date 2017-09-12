# -*- coding: utf-8 -*-
# %matplotlib qt
# import matplotlib.pyplot as plt
import datetime
import os.path
import numpy as np
from scipy.optimize import curve_fit
from mantid.simpleapi import (mtd, ConjoinWorkspaces, Load, ConvertUnits,
                              ExtractSingleSpectrum, SaveNexusProcessed,
                              DeleteWorkspace, RebinToWorkspace,
                              RenameWorkspace, Rebin, LoadMask, CloneWorkspace,
                              SumSpectra, MaskDetectors, GroupWorkspaces,
                              CreateWorkspace, DeleteWorkspaces, WeightedMean,
                              Fit)
from .runtypes import HeData


def int3samples(runs, name, masks, binning='0.5, 0.05, 8.0'):
    """
    Finds the polarisation versus wavelength for a set of detector tubes.

    Parameters
    ----------
    runs: list of RunData objects
      The runs whose polarisation we are interested in.

    name: string
      The name of this set of runs

    masks: list of string
      The file names of the masks for the sequential tubes that are being used
      for the SEMSANS measurements.

    binning: string
      The binning values to use for the wavelength bins.  The default value is
      '0.5, 0.025, 10.0'
    """
    for tube, _ in enumerate(masks):
        for i in [1, 2]:
            final_state = "{}_{}_{}".format(name, tube, i)
            if final_state in mtd.getObjectNames():
                DeleteWorkspace(final_state)

    for rnum in runs:
        w1 = Load(BASE.format(rnum.number), LoadMonitors=True)
        w1mon = ExtractSingleSpectrum('w1_monitors', 0)
        w1 = ConvertUnits('w1', 'Wavelength', AlignBins=1)
        w1mon = ConvertUnits(w1mon, 'Wavelength')
        w1 = Rebin(w1, binning, PreserveEvents=False)
        w1mon = Rebin(w1mon, binning)
        w1 = w1 / w1mon
        for tube, mask in enumerate(masks):
            Mask_Tube = LoadMask('LARMOR', mask)
            w1temp = CloneWorkspace(w1)
            MaskDetectors(w1temp, MaskedWorkspace="Mask_Tube")
            Tube_Sum = SumSpectra(w1temp)
            for i in [1, 2]:
                final_state = "{}_{}_{}".format(name, tube, i)
                if final_state in mtd.getObjectNames():
                    mtd[final_state] += mtd["Tube_Sum_{}".format(i)]
                else:
                    mtd[final_state] = mtd["Tube_Sum_{}".format(i)]

    x = mtd["{}_0_1".format(name)].extractX()[0]
    dx = (x[1:] + x[:-1]) / 2
    pols = []

    for run in runs:
        he_stat = he3_stats(run)
        start = (run.start-he_stat.dt).seconds/3600/he_stat.t1
        end = (run.end-he_stat.dt).seconds/3600/he_stat.t1
        for time in np.linspace(start, end, 10):
            temp = he3pol(he_stat.scale, time)(dx)
            pols.append(temp)
    wpol = CreateWorkspace(x, np.mean(pols, axis=0),
                           # and the blank
                           UnitX="Wavelength",
                           YUnitLabel="Counts")

    for tube, _ in enumerate(masks):
        up = mtd["{}_{}_2".format(name, tube)]
        dn = mtd["{}_{}_1".format(name, tube)]
        pol = (up - dn) / (up + dn)
        pol /= wpol
        DeleteWorkspaces(["{}_{}_{}".format(name, tube, i)
                          for i in range(1, 3)])
        RenameWorkspace("pol",
                        OutputWorkspace="{}_{}".format(name, tube))
    DeleteWorkspaces(["Tube_Sum_1", "Tube_Sum_2"])

    GroupWorkspaces(["{}_{}".format(name, tube)
                     for tube, _ in enumerate(masks)
                     for i in range(1, 3)],
                    OutputWorkspace=str(name))


def norm(sample, blank, masks):
    """
    Normalise the neutron polarisation on a tube by tube basis

    Parameters
    ----------
    sample: string
      The name of the sample to be normalised.  The individual tubes are
      assumed to be in workspaces with names like sample_2
    blank: string
      The name of the blank to be normalised agains.  The individual tubes are
      assumed to be in workspaces with names like blank_2
    masks: list of string
      The file names for the masks used for the individual tubes.
    """
    for t, _ in enumerate(masks):
        wtemp = mtd[sample + "_{}".format(t)] / \
            mtd[blank + "_{}".format(t)]

        y = mtd[blank + "_{}".format(t)].extractY()
        e = wtemp.extractE()

        e[np.abs(y) < 0.2] *= 1e9
        wtemp.setE(0, e[0])

        RenameWorkspace("wtemp", sample + "_{}_norm".format(t))
    wtemp = WeightedMean(sample + "_0_norm",
                         sample + "_1_norm")
    for tube in range(2, len(masks)):
        wtemp = WeightedMean(wtemp, sample + "_{}_norm".format(tube))
    RenameWorkspace(wtemp, OutputWorkspace=sample + "_Norm")
    DeleteWorkspaces(["{}_{}_norm".format(sample, tube)
                      for tube, _ in enumerate(masks)])
