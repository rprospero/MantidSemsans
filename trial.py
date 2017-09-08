from Semsans.metadata import get_log, get_he3_log, RUN_IDENTIFIERS
from Semsans.full_analysis import analyse

###############################################
# Computer specific variables
#
# You will need to change these values for this
# script to run on your computer
#
###############################################

# Fold where we will save the Sans batch script
save_path = "C:/Users/auv61894/Documents/Science/Edler_May_2017/"

# The location of the 3He log file
he_log = r"C:\Users\auv61894\Dropbox\Science\Edler\Edler_May_2017\heruns.tsv"


###############################################
# Run specific variables
#
# These will need to be changed with each
# setup of the combined Sans/Semsans instrument
#
###############################################


# The mask files for the individual tubes
masks = [r'\\isis\inst$\NDXLARMOR\User\Users\Edler\May_2017\Mask_Tube39.xml',
         r'\\isis\inst$\NDXLARMOR\User\Users\Edler\May_2017\Mask_Tube40.xml',
         r'\\isis\inst$\NDXLARMOR\User\Users\Edler\May_2017\Mask_Tube41.xml']


###############################################
# Main script
###############################################

# Load the 3He log into mantid so that we can
# normalise the polarisation.
get_he3_log(he_log)

# Describe the titles of the SANS runs
# with a regex. The value in the parens
# will be used to get the name of the
# actual sample.
# RUN_IDENTIFIERS["run"] = r'(.+)_run:_\d+_SANS'
RUN_IDENTIFIERS["run"] = r'Semsans_Sans_(.+)_WP1_.+_SANS'
RUN_IDENTIFIERS["trans"] = r'Semsans_Sans_(.+)_WP1_.+_TRANS'
RUN_IDENTIFIERS["can_sans"] = r'Semsans_Sans_D2O_WP1_.+_SANS'
RUN_IDENTIFIERS["can_trans"] = r'Semsans_Sans_D2O_WP1_.+_TRANS'
RUN_IDENTIFIERS["direct_sans"] = r'Semsans_Sans_Blank_WP1_.+_SANS'
RUN_IDENTIFIERS["direct_trans"] = r'Semsans_Sans_Blank_WP1_.+_TRANS'

# Load the information about the runs of interest
# from the Larmor log.  This particular measurement
# spanned from run 20401 to 20535
get_log(range(20282, 20310))

# Find the semsans values for two of the samples.
# This will also produce two csv files that can be
# imported into the ISIS SANS gui to retrieve
# the Sans data.
# analyse("OEGC 25C R_10.81_runs", masks,
#         save_path+"oegc_10.81_runs.csv")
# analyse("metadata_CTAB_25_R_7.21_runs", masks,
#         save_path+"ctab_7.21_runs.csv")
analyse("metadata_EDH11_runs", masks, save_path+"EDH11_runs.csv")
analyse("metadata_EDH2_runs", masks, save_path+"EDH2_runs.csv")
analyse("metadata_SD10_runs", masks, save_path+"SD10_runs.csv")
analyse("metadata_SD1_runs", masks, save_path+"SD1_runs.csv")
analyse("metadata_SDS8_runs", masks, save_path+"SDS8_runs.csv")

# Load supermirror runs instead
# RUN_IDENTIFIERS["run"] = r"(Supermirror).+_SANS"

# Re-examine the log file with the new definition
# of how a sample run's title will look.  This
# will pull out the supermirror run files
# get_log(range(20401, 20536))

# Analyse the supermirror runs
# analyse("Supermirror_runs", masks,
#         save_path+"mirror_runs.csv")
