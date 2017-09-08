# -*- coding: utf-8 -*-
from mantid.kernel import *
from mantid.api import *
from runtypes import HeData
import numpy as np
import datetime


class SemsansNorm(PythonAlgorithm):
    def category(self):
        return "SESANS"

    def PyInit(self):
        self.declareProperty(name="SampleTitle", defaultValue="")
        self.declareProperty(
            WorkspaceProperty(name="HeliumLogTable", defaultValue="",
                              direction=Direction.Input))
        self.declareProperty(
            WorkspaceProperty(name="LogTable", defaultValue="",
                              direction=Direction.Input))
        self.declareProperty(
            WorkGroupProperty(name="Blank", direction=Direction.Input,
                              defaultValue=""))

        self.declareProperty(
            FileProperty(name="FirstMask", defaultValue="",
                         action=FileAction.Load))
        self.declareProperty(name="OtherMasks", defaultValue="")

    def PyExec(self):
