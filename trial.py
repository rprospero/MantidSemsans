from Semsans.metadata import get_log, get_he3_log, RUN_IDENTIFIERS
from Semsans.full_analysis import analyse

save_path = "C:/Users/auv61894/Dropbox/Science/Edler/Edler_May_2017/"
mask_path = r'\\isis\inst$\NDXLARMOR\User\Users\Edler\May_2017\Mask_Tube{}.xml'
masks = [mask_path.format(t) for t in [39, 40, 41]]

get_he3_log(
    r"C:\Users\auv61894\Dropbox\Science\Edler\Edler_May_2017\heruns.tsv")
get_log(range(20387, 20536))
analyse("OEGC 25C R_10.81_runs", masks,
        save_path+"oegc_10.81_runs.csv")
analyse("CTAB 25 R_7.21_runs", masks,
        save_path+"ctab_7.21_runs.csv")

#Load supermirror runs instead
RUN_IDENTIFIERS["run"] = r"(Supermirror).+_SANS"

get_log(range(20387, 20536))
analyse("Supermirror_runs", masks,
        save_path+"mirror_runs.csv")
