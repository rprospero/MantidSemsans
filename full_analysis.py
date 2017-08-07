from os.path import join, exists
import tempfile
import sans.command_interface.ISISCommandInterface as ici
from mantid.api import mtd
from mantid.simpleapi import SaveAscii, DeleteWorkspace, DeleteWorkspaces
from .Semsans import sumToShim, sel_const, int3samples, norm, sel
from .runtypes import table_to_run

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

def analyse(data_table, blank_table, output_file, show_fits=False, show_quality=False):
    if "Full Blank" not in mtd.getObjectNames():
        int3samples(table_to_run(blank_table), "Full Blank", MASKS)
    const = sel_const([mtd["Full Blank_{}".format(t)]
                    for t, _ in enumerate(MASKS)],
                      show_fits=show_fits, show_quality=show_quality)

    k = data_table[:-5]
    runs = table_to_run(mtd[data_table])
    for idx, run in enumerate(runs):
        int3samples([run], "{}_run{:02d}".format(k, idx), MASKS)
        # DeleteWorkspace("{}_sans_nxs".format(run.number))
        semsans_ws = "{}_run{:02d}".format(k, idx)
        norm(semsans_ws, "Full Blank", MASKS)
        sel(semsans_ws+"_norm", const)
        # SaveAscii(semsans_ws+"_norm_sel",
        #           join(SAVE_PATH,"{}_run{:02d}_semsans.dat".format(k,idx)))
        DeleteWorkspaces([semsans_ws,
                          semsans_ws+"_Norm"])
    # with tempfile.NamedTemporaryFile(delete=False) as outfile:
    with open(output_file, "w") as outfile:
        framework = "sample_sans,{}-add," \
                    "sample_trans,{}-add," \
                    "sample_direct_beam,{}-add,"\
                    "can_sans,{}-add,"\
                    "can_trans,{}-add,"\
                    "can_direct_beam,{}-add,"\
                    "output_as,test_{}\n"
        for idx, run in enumerate(runs):
            outfile.write(
                framework.format(run.number, run.trans, run.direct,
                                 run.csans, run.ctrans, run.direct,
                                 idx))
    # ici.UseCompatibilityMode()
    # ici.MaskFile(MASK)
    # ici.BatchReduce(output_file, ".nxs", saveAlgs={})
    print("Done")
