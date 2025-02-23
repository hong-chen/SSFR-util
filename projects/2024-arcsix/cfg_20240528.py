import datetime
import ssfr

# parameters that need frequent change
#╭────────────────────────────────────────────────────────────────────────────╮#
date = datetime.datetime(2024, 5, 28)
operator = 'Vikas Nataraja'
mission = 'arcsix'
year = '2024'
platform = 'p3b'
comments = '1st research flight, had clear-sky spiral'

hsk_tag  = 'hsk'
alp_tag  = 'alp'
hsr1_tag = 'hsr1-a'
ssfr_tag = 'ssfr-a'
ssrr_tag = 'ssfr-b'

alp_time_offset  = -17.19
hsr1_time_offset = 0.0
ssfr_time_offset = -156.26
ssrr_time_offset = -222.66

alp_ang_pit_offset = 0.0
alp_ang_rol_offset = 0.0
hsr1_ang_pit_offset = 0.0
hsr1_ang_rol_offset = 0.0

fdir_data = 'data/%s/%s/%s' % (mission, year, platform)
fdir_cal = 'data/%s/cal' % mission
fdir_out = 'data/%s/processed' % mission

# parameters that require extra processing
#╭──────────────────────────────────────────────────────────────╮#
# data directory
#╭────────────────────────────────────────────────╮#
fdir_hsk = '%s/aux' % (fdir_data)
fdir_alp = ssfr.util.get_all_folders(fdir_data, pattern='*%4.4d*%2.2d*%2.2d*raw?%s' % (date.year, date.month, date.day, alp_tag))[-1]
fdir_hsr1 = ssfr.util.get_all_folders(fdir_data, pattern='*%4.4d*%2.2d*%2.2d*raw?%s' % (date.year, date.month, date.day, hsr1_tag))[-1]
fdir_ssfr = ssfr.util.get_all_folders(fdir_data, pattern='*%4.4d*%2.2d*%2.2d*raw?%s' % (date.year, date.month, date.day, ssfr_tag))[-1]
fdir_ssrr = ssfr.util.get_all_folders(fdir_data, pattern='*%4.4d*%2.2d*%2.2d*raw?%s' % (date.year, date.month, date.day, ssrr_tag))[-1]
#╰────────────────────────────────────────────────╯#

# data files
#╭────────────────────────────────────────────────╮#
fname_hsk = ssfr.util.get_all_files(fdir_hsk, pattern='*%4.4d*%2.2d*%2.2d*.???' % (date.year, date.month, date.day))[-1]
fnames_alp = ssfr.util.get_all_files(fdir_alp, pattern='*.plt3')
fnames_hsr1 = ssfr.util.get_all_files(fdir_hsr1, pattern='*.txt')
fnames_ssfr = ssfr.util.get_all_files(fdir_ssfr, pattern='*.SKS')
fnames_ssrr = ssfr.util.get_all_files(fdir_ssrr, pattern='*.SKS')
#╰────────────────────────────────────────────────╯#

# calibrations
#╭────────────────────────────────────────────────╮#
#╰────────────────────────────────────────────────╯#
#╰──────────────────────────────────────────────────────────────╯#
#╰────────────────────────────────────────────────────────────────────────────╯#


# common settings
#╭────────────────────────────────────────────────────────────────────────────╮#
common = {
        'date': date,
        'date_s': date.strftime('%Y%m%d'),
        'date_s_': date.strftime('%Y-%m-%d'),
        'mission': mission.lower(),
        'platform': platform.lower(),
        'operator': operator,
        'comments': comments,
        }
#╰────────────────────────────────────────────────────────────────────────────╯#



# House Keeping File
#╭────────────────────────────────────────────────────────────────────────────╮#
hsk = {
        'tag': hsk_tag.lower(),
        'fname': fname_hsk,
        }
#╰────────────────────────────────────────────────────────────────────────────╯#



# Hyper-Spectral Radiometer 1
#╭────────────────────────────────────────────────────────────────────────────╮#
hsr1 = {
        'tag': hsr1_tag.lower(),
        'fnames': fnames_hsr1,
        'ang_pit_offset': hsr1_ang_pit_offset,
        'ang_rol_offset': hsr1_ang_rol_offset,
        }
#╰────────────────────────────────────────────────────────────────────────────╯#



# Active Leveling Platform
#╭────────────────────────────────────────────────────────────────────────────╮#
alp = {
        'tag': alp_tag.lower(),
        'fnames': fnames_alp,
        'time_offset': alp_time_offset,
        'ang_pit_offset': alp_ang_pit_offset,
        'ang_rol_offset': alp_ang_rol_offset,
        }
#╰────────────────────────────────────────────────────────────────────────────╯#



# Solar Spectral Flux Radiometer
#╭────────────────────────────────────────────────────────────────────────────╮#
ssfr = {
        'tag': ssfr_tag.lower(),

        'fnames': fnames_ssfr,

        'fname_rad_cal': fname_rad_cal_ssfr,

        'which_ssfr': 'lasp|%s' % ssfr_tag.lower(),

        # zenith wavelength setting
        'wvl_s_zen': 350.0,  # beginning/first wavelength [nm] of the selected wavelength range
        'wvl_e_zen': 2000.0, # ending/last wavelength [nm] of the selected wavelength range
        'wvl_j_zen': 950.0,  # joinder wavelength within the overlapping wavelength coverage between Silicon and InGaAs spectrometers

        # nadir wavelength setting
        'wvl_s_nad': 350.0,  # beginning/first wavelength [nm] of the selected wavelength range
        'wvl_e_nad': 2000.0, # ending/last wavelength [nm] of the selected wavelength range
        'wvl_j_nad': 950.0,  # joinder wavelength within the overlapping wavelength coverage between Silicon and InGaAs spectrometers

        # time offset [seconds]
        'time_offset': 0.0,

        # number of data points to be excluded at the beginning and end of a dark cycle (due to slow shutter closing/opening glitch)
        'dark_extend': 1,

        # number of data points to be excluded at the beginning and end of a light cycle (due to slow shutter closing/opening glitch)
        'light_extend': 1,

        # dark correction mode: `interp`, linear interpolation using two adjacent dark cycles
        #   also available in `mean`, which uses the average to represent darks
        #   generally, `interp` is preferred
        'dark_corr_mode': 'interp',

        # minimum number of darks to achieve valid dark correction
        'dark_threshold': 5,

        # minimum number of lights to achieve valid dark correction
        'light_threshold': 10,
        }
#╰────────────────────────────────────────────────────────────────────────────╯#



# Solar Spectral "Radiance" Radiometer
#╭────────────────────────────────────────────────────────────────────────────╮#
ssrr = {
        'tag': ssrr_tag.lower(),

        'fnames': fnames_ssrr,

        'fname_ssrr_rad_cal': None,

        'which_ssfr': 'lasp|%s' % ssrr_tag.lower(),

        # zenith wavelength setting
        'wvl_s_zen': 350.0,  # beginning/first wavelength [nm] of the selected wavelength range
        'wvl_e_zen': 2000.0, # ending/last wavelength [nm] of the selected wavelength range
        'wvl_j_zen': 950.0,  # joinder wavelength within the overlapping wavelength coverage between Silicon and InGaAs spectrometers

        # nadir wavelength setting
        'wvl_s_nad': 350.0,  # beginning/first wavelength [nm] of the selected wavelength range
        'wvl_e_nad': 2000.0, # ending/last wavelength [nm] of the selected wavelength range
        'wvl_j_nad': 950.0,  # joinder wavelength within the overlapping wavelength coverage between Silicon and InGaAs spectrometers

        # time offset [seconds]
        'time_offset': 0.0,

        # number of data points to be excluded at the beginning and end of a dark cycle (due to slow shutter closing/opening glitch)
        'dark_extend': 1,

        # number of data points to be excluded at the beginning and end of a light cycle (due to slow shutter closing/opening glitch)
        'light_extend': 1,

        # dark correction mode: `interp`, linear interpolation using two adjacent dark cycles
        #   also available in `mean`, which uses the average to represent darks
        #   generally, `interp` is preferred
        'dark_corr_mode': 'interp',

        # minimum number of darks to achieve valid dark correction
        'dark_threshold': 5,

        # minimum number of lights to achieve valid dark correction
        'light_threshold': 10,
        }
#╰────────────────────────────────────────────────────────────────────────────╯#
