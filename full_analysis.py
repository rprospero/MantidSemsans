import datetime
from os.path import join, expanduser, exists
import sans.command_interface.ISISCommandInterface as ici
from mantid.api import mtd
from mantid.simpleapi import SaveAscii, DeleteWorkspace, DeleteWorkspaces
import json
from collections import namedtuple
from .Semsans import sumToShim, sel_const, int3samples, norm, sel, sel_const
from .runtypes import HeData, RunData

def get_shimed(run, path, reload=False):
    f =  join(path, "LARMOR{:08d}-add.nxs".format(run))
    if reload or not exists(f):
        sumToShim(run, path)
    return f

def get_sans(run, trans, sans_can, trans_can, direct, mask, path):
    ici.UseCompatibilityMode()
    ici.LARMOR()
    ici.Set1D()
    ici.MaskFile(mask)
    ici.AssignSample(get_shimed(run, path))
    ici.AssignCan(get_shimed(sans_can, path))
    ici.TransmissionSample(get_shimed(trans, path),
                           get_shimed(direct, path))
    ici.TransmissionCan(get_shimed(trans_can, path),
                        get_shimed(direct, path))
    ici.WavRangeReduction(None, None, ici.DefaultTrans)
    # SaveNexus(mtd["{}rear_1D_0.9_12.5".format(run)],
    #                 join(base_dir,
    #                 "{}_1D.nxs".format(run)))

SAVE_PATH="C:\\Users\\auv61894\\Documents\\Science\\Edler_May_2017\\"
MASK = r"\\isis\inst$\NDXLARMOR\User"\
       "\Users\Masks\USER_Edler_171B_a2_8mm_SEMSANS_r20287.txt"
TUBES = [39, 40, 41]
MASK_PATH = r'\\isis\inst$\NDXLARMOR\User\Users\Edler\May_2017\Mask_Tube{}.xml'

MASKS = [MASK_PATH.format(t) for t in TUBES]

def analyse(data_table):
    runs = [
        RunData(x["Run Number"], x["Sample"], x["Scale"], x["He3 Start"],
                x["He3 End"], x["Trans run"], x["Can Sans run"],
                x["Can Trans run"], x["Direct Trans run"],
                datetime.datetime.strptime(x["Start time"],
                                           "%Y-%m-%dT%H:%M:%S"))
        for x in mtd[data_table]]


    if "Full Blank" not in mtd.getObjectNames():
        int3samples(d["Full Blank"], "Full Blank", MASKS)
    const = sel_const([mtd["Full Blank_{}".format(t)]
                    for t, _ in enumerate(MASKS)],
                    show_fits=True, show_quality=True)

    k = data_table[:-5]
    for idx, run in enumerate(runs):
        # Mantid handles sans pretty well on its own, so we'll skip it for right now
        # get_sans(run.number, run.trans, run.csans, run.ctrans, run.direct, MASK, SAVE_PATH)
        # sans_ws = "{}rear_1D_0.9_10.0".format(run.number)
        # SaveAscii(sans_ws, join(SAVE_PATH,"{}_run{:02d}_sans.dat".format(k,idx)))
        # DeleteWorkspaces([sans_ws, sans_ws+"_lab_can", sans_ws+"_lab_can_count"
        #                 ,sans_ws+"_lab_can_norm"])
        # DeleteWorkspace("{}_sans_nxs_monitors".format(run.number))
        int3samples([run], "{}_run{:02d}".format(k, idx), MASKS)
        # DeleteWorkspace("{}_sans_nxs".format(run.number))
        semsans_ws = "{}_run{:02d}".format(k, idx)
        norm(semsans_ws, "Full Blank", MASKS)
        sel(semsans_ws+"_norm", const)
        # SaveAscii(semsans_ws+"_norm_sel",
        #           join(SAVE_PATH,"{}_run{:02d}_semsans.dat".format(k,idx)))
        DeleteWorkspaces([semsans_ws,
                            semsans_ws+"_Norm"])
