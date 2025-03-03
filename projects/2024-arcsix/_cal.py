"""
Code for processing data collected by SSFR Team during NASA ARCSIX 2024.

SSFR-A: Solar Spectral Flux Radiometer - Alvin
SSFR-B: Solar Spectral Flux Radiometer - Belana
HSR1-A: Hyper-Spectral Radiometer 1 - Alvin
HSR1-B: Hyper-Spectral Radiometer 1 - Belana
ALP: Active Leveling Platform

Acknowledgements:
    Instrument engineering:
        Jeffery Drouet, Sebastian Schmidt
    Pre-mission and post-mission calibration and data analysis:
        Hong Chen, Yu-Wen Chen, Ken Hirata, Vikas Nataraja, Sebastian Schmidt, Bruce Kindel
    In-field calibration and on-flight operation:
        Vikas Nataraja, Arabella Chamberlain, Ken Hirata, Sebastian Becker, Jeffery Drouet, Sebastian Schmidt
"""

import os
import sys
import glob
import datetime
import warnings
import importlib
from collections import OrderedDict
from tqdm import tqdm
import h5py
import numpy as np
from scipy import interpolate
from scipy.io import readsav
from scipy.optimize import curve_fit
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.path as mpl_path
import matplotlib.image as mpl_img
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib import rcParams, ticker
from matplotlib.ticker import FixedLocator
from mpl_toolkits.axes_grid1 import make_axes_locatable
# import cartopy.crs as ccrs
# mpl.use('Agg')



import ssfr


# parameters
#╭────────────────────────────────────────────────────────────────────────────╮#
_MISSION_     = 'arcsix'
_PLATFORM_    = 'p3b'

_HSK_         = 'hsk'
_ALP_         = 'alp'
_SSFR1_       = 'ssfr-a'
_SSFR2_       = 'ssfr-b'
_CAM_         = 'nac'

_SPNS_        = 'spns-a'
_WHICH_SSFR_ = 'ssfr-a'
# _SPNS_        = 'spns-b'
# _WHICH_SSFR_ = 'ssfr-b'

_FDIR_HSK_   = 'data/arcsix/2024/p3/aux/hsk'
_FDIR_CAL_   = 'data/%s/cal' % _MISSION_

_FDIR_DATA_  = 'data/%s' % _MISSION_
_FDIR_OUT_   = '%s/processed' % _FDIR_DATA_

_VERBOSE_   = True
_FNAMES_ = {}
#╰────────────────────────────────────────────────────────────────────────────╯#


# functions for ssfr calibrations
#╭────────────────────────────────────────────────────────────────────────────╮#
def wvl_cal_old(ssfr_tag, lc_tag, lamp_tag, Nchan=256):

    fdir_data = '/argus/field/arcsix/cal/wvl-cal'

    indices_spec = {
            'zen': [0, 1],
            'nad': [2, 3]
            }

    fdir =  sorted(glob.glob('%s/*%s*%s*%s*' % (fdir_data, ssfr_tag, lc_tag, lamp_tag)))[0]
    fnames = sorted(glob.glob('%s/*00001.SKS' % (fdir)))

    ssfr0 = ssfr.lasp_ssfr.read_ssfr(fnames, dark_corr_mode='interp')

    xchan = np.arange(Nchan)

    spectra0 = np.nanmean(ssfr0.dset0['spectra_dark-corr'][:, :, indices_spec[lc_tag]], axis=0)
    spectra1 = np.nanmean(ssfr0.dset1['spectra_dark-corr'][:, :, indices_spec[lc_tag]], axis=0)

    # spectra_inp = {lamp_tag.lower(): spectra0[:, 0]}
    # ssfr.cal.cal_wvl_coef(spectra_inp, which_spec='lasp|%s|%s|si' % (ssfr_tag.lower(), lc_tag.lower()))

    spectra_inp = {lamp_tag.lower(): spectra0[:, 1]}
    ssfr.cal.cal_wvl_coef(spectra_inp, which_spec='lasp|%s|%s|in' % (ssfr_tag.lower(), lc_tag.lower()))
    sys.exit()

    # figure
    #╭────────────────────────────────────────────────────────────────────────────╮#
    if True:
        plt.close('all')
        fig = plt.figure(figsize=(12, 6))
        fig.suptitle('%s %s (illuminated by %s Lamp)' % (ssfr_tag.upper(), lc_tag.title(), lamp_tag.upper()))
        # plot
        #╭──────────────────────────────────────────────────────────────╮#
        ax1 = fig.add_subplot(121)
        ax1.plot(xchan, spectra0[:, 0], lw=1, c='r')
        ax1.plot(xchan, spectra1[:, 0], lw=1, c='b')
        ax1.set_xlabel('Channel #')
        ax1.set_ylabel('Counts')
        ax1.set_ylim(bottom=0)
        ax1.set_title('Silicon')

        ax2 = fig.add_subplot(122)
        ax2.plot(xchan, spectra0[:, 1], lw=1, c='r')
        ax2.plot(xchan, spectra1[:, 1], lw=1, c='b')
        ax2.set_xlabel('Channel #')
        ax2.set_ylabel('Counts')
        ax2.set_ylim(bottom=0)
        ax2.set_title('InGaAs')
        #╰──────────────────────────────────────────────────────────────╯#

        patches_legend = [
                          mpatches.Patch(color='red' , label='IntTime set 1'), \
                          mpatches.Patch(color='blue', label='IntTime set 2'), \
                         ]
        ax1.legend(handles=patches_legend, loc='upper right', fontsize=16)

        # save figure
        #╭──────────────────────────────────────────────────────────────╮#
        fig.subplots_adjust(hspace=0.3, wspace=0.3)
        _metadata = {'Computer': os.uname()[1], 'Script': os.path.abspath(__file__), 'Function':sys._getframe().f_code.co_name, 'Date':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        fig.savefig('%s_%s_%s_%s.png' % (_metadata['Function'], ssfr_tag.lower(), lc_tag.lower(), lamp_tag.lower()), bbox_inches='tight', metadata=_metadata)
        #╰──────────────────────────────────────────────────────────────╯#
    #╰────────────────────────────────────────────────────────────────────────────╯#

def rad_cal_old(ssfr_tag, lc_tag, lamp_tag, Nchan=256):

    fdir_data = 'data/arcsix/cal/rad-cal'

    indices_spec = {
            'zen': [0, 1],
            'nad': [2, 3]
            }

    fdir =  sorted(glob.glob('%s/*%s*%s*%s*' % (fdir_data, ssfr_tag, lc_tag, lamp_tag)))[0]
    fnames = sorted(glob.glob('%s/*00001.SKS' % (fdir)))

    date_cal_s   = '2023-11-16'
    date_today_s = datetime.datetime.now().strftime('%Y-%m-%d')

    ssfr_ = ssfr.lasp_ssfr.read_ssfr(fnames)
    for i in range(ssfr_.Ndset):
        dset_tag = 'dset%d' % i
        dset_ = getattr(ssfr_, dset_tag)
        int_time = dset_['info']['int_time']

        fname = '%s/cal/%s|cal-rad-pri|lasp|%s|%s|%s-si%3.3d-in%3.3d|%s.h5' % (ssfr.common.fdir_data, date_cal_s, ssfr_tag.lower(), lc_tag.lower(), dset_tag.lower(), int_time['%s|si' % lc_tag], int_time['%s|in' % lc_tag], date_today_s)
        f = h5py.File(fname, 'w')

        resp_pri = ssfr.cal.cal_rad_resp(fnames, which_ssfr='lasp|%s' % ssfr_tag.lower(), which_lc=lc_tag.lower(), int_time=int_time, which_lamp=lamp_tag.lower())

        for key in resp_pri.keys():
            f[key] = resp_pri[key]

        f.close()

def ang_cal_old(fdir):

    """

    Notes:
        angular calibration is done for three different azimuth angles (reference to the vaccum port)
        60, 180, 300

        angles
    """

    tags = os.path.basename(fdir).split('_')
    ssfr_tag = tags[1]
    lc_tag   = tags[2]

    # get angles
    #╭────────────────────────────────────────────────────────────────────────────╮#
    angles_pos = np.concatenate((np.arange(0.0, 30.0, 3.0), np.arange(30.0, 50.0, 5.0), np.arange(50.0, 91.0, 10.0)))
    angles_neg = -angles_pos
    angles = np.concatenate((angles_pos, angles_neg, np.array([0.0])))
    #╰────────────────────────────────────────────────────────────────────────────╯#

    # make fnames, a dictionary <key:value> with file name as key, angle as value
    #╭────────────────────────────────────────────────────────────────────────────╮#
    fnames_ = sorted(glob.glob('%s/*.SKS' % fdir))
    fnames  = {
            fnames_[i]: angles[i] for i in range(angles.size)
            }
    #╰────────────────────────────────────────────────────────────────────────────╯#

    date_today_s = datetime.datetime.now().strftime('%Y-%m-%d')

    ssfr_ = ssfr.lasp_ssfr.read_ssfr([fnames_[0]])
    for i in range(ssfr_.Ndset):
        dset_tag = 'dset%d' % i
        dset_ = getattr(ssfr_, dset_tag)
        int_time = dset_['info']['int_time']

        filename_tag = '%s|%s|%s|%s' % (tags[0], tags[4], date_today_s, dset_tag)

        ssfr.cal.cdata_ang_resp(fnames, filename_tag=filename_tag, which_ssfr='lasp|%s' % ssfr_tag, which_lc=lc_tag, int_time=int_time)

def main_calibration_old():

    """
    Notes:
        irradiance setup:
            SSFR-A (Alvin)
              - nadir : LC6 + stainless steel cased fiber
              - zenith: LC4 + black plastic cased fiber
    """

    # wavelength calibration
    #╭────────────────────────────────────────────────────────────────────────────╮#
    # for ssfr_tag in ['SSFR-A', 'SSFR-B']:
    #     for lc_tag in ['zen', 'nad']:
    #         for lamp_tag in ['kr', 'hg']:
    #             wvl_cal(ssfr_tag, lc_tag, lamp_tag)
    #╰────────────────────────────────────────────────────────────────────────────╯#

    # radiometric calibration
    #╭────────────────────────────────────────────────────────────────────────────╮#
    for ssfr_tag in ['SSFR-A', 'SSFR-B']:
        for lc_tag in ['zen', 'nad']:
            for lamp_tag in ['1324']:
                rad_cal(ssfr_tag, lc_tag, lamp_tag)
    #╰────────────────────────────────────────────────────────────────────────────╯#

    # angular calibration
    #╭────────────────────────────────────────────────────────────────────────────╮#
    # fdirs = [
    #         '/argus/field/arcsix/cal/ang-cal/2024-03-19_SSFR-A_zen-lc4_ang-cal_vaa-060_lamp-507_si-080-120_in-250-350',
    #         '/argus/field/arcsix/cal/ang-cal/2024-03-15_SSFR-A_zen-lc4_ang-cal_vaa-180_lamp-507_si-080-120_in-250-350',
    #         '/argus/field/arcsix/cal/ang-cal/2024-03-19_SSFR-A_zen-lc4_ang-cal_vaa-300_lamp-507_si-080-120_in-250-350',
    #         '/argus/field/arcsix/cal/ang-cal/2024-03-18_SSFR-A_nad-lc6_ang-cal_vaa-060_lamp-507_si-080-120_in-250-350',
    #         '/argus/field/arcsix/cal/ang-cal/2024-03-18_SSFR-A_nad-lc6_ang-cal_vaa-180_lamp-507_si-080-120_in-250-350',
    #         '/argus/field/arcsix/cal/ang-cal/2024-03-18_SSFR-A_nad-lc6_ang-cal_vaa-300_lamp-507_si-080-120_in-250-350',
    #         ]
    # for fdir in fdirs:
    #     ang_cal(fdir)
    #╰────────────────────────────────────────────────────────────────────────────╯#
    sys.exit()
#╰────────────────────────────────────────────────────────────────────────────╯#


# radiometric calibrations (1. primary, 2. transfer, 3. secondary)
#╭────────────────────────────────────────────────────────────────────────────╮#
def retrieve_rad_cal(
        date,
        which_ssfr='lasp|ssfr-a',
        which_ssfr_for_flux='lasp|ssfr-a',
        run=True,
        ):

    """
    version 1: 1) time adjustment          : check for time offset and merge SSFR data with aircraft housekeeping data
               2) time synchronization     : interpolate raw SSFR data into the time frame of the housekeeping data
               3) counts-to-flux conversion: apply primary and secondary calibration to convert counts to fluxes
    """

    date_s = date.strftime('%Y%m%d')

    for idset in np.unique(dset_num):

        if which_ssfr_for_flux == which_ssfr:
            # select calibration file (can later be adjusted for different integration time sets)
            #╭──────────────────────────────────────────────────────────────╮#
            fdir_cal = '%s/rad-cal' % _FDIR_CAL_

            jday_today = ssfr.util.dtime_to_jday(date)

            int_time_tag_zen = 'si-%3.3d|in-%3.3d' % (data_ssfr_v0['raw/int_time'][data_ssfr_v0['raw/dset_num']==idset][0, 0], data_ssfr_v0['raw/int_time'][data_ssfr_v0['raw/dset_num']==idset][0, 1])
            int_time_tag_nad = 'si-%3.3d|in-%3.3d' % (data_ssfr_v0['raw/int_time'][data_ssfr_v0['raw/dset_num']==idset][0, 2], data_ssfr_v0['raw/int_time'][data_ssfr_v0['raw/dset_num']==idset][0, 3])

            # fnames_cal_zen = sorted(ssfr.util.get_all_files(fdir_cal, pattern='*lamp-1324|*lamp-150c_after-pri|*pituffik*%s*zen*%s*' % (which_ssfr_for_flux.lower(), int_time_tag_zen)), key=os.path.getmtime)
            fnames_cal_zen = sorted(ssfr.util.get_all_files(fdir_cal, pattern='*lamp-1324|*lamp-150c*|*pituffik*%s*zen*%s*' % (which_ssfr_for_flux.lower(), int_time_tag_zen)), key=os.path.getmtime)
            jday_cal_zen = np.zeros(len(fnames_cal_zen), dtype=np.float64)
            for i in range(jday_cal_zen.size):
                dtime0_s = os.path.basename(fnames_cal_zen[i]).split('|')[2].split('_')[0]
                dtime0 = datetime.datetime.strptime(dtime0_s, '%Y-%m-%d')
                jday_cal_zen[i] = ssfr.util.dtime_to_jday(dtime0) + i/86400.0
            fname_cal_zen = fnames_cal_zen[np.argmin(np.abs(jday_cal_zen-jday_today))]
            data_cal_zen = ssfr.util.load_h5(fname_cal_zen)

            msg = '\nMessage [cdata_ssfr_v1]: Using <%s> for %s zenith irradiance ...' % (os.path.basename(fname_cal_zen), which_ssfr.upper())
            print(msg)

            # fnames_cal_nad = sorted(ssfr.util.get_all_files(fdir_cal, pattern='*lamp-1324|*lamp-150c_after-pri|*pituffik*%s*nad*%s*' % (which_ssfr_for_flux.lower(), int_time_tag_nad)), key=os.path.getmtime)
            fnames_cal_nad = sorted(ssfr.util.get_all_files(fdir_cal, pattern='*lamp-1324|*lamp-150c*|*pituffik*%s*nad*%s*' % (which_ssfr_for_flux.lower(), int_time_tag_nad)), key=os.path.getmtime)
            jday_cal_nad = np.zeros(len(fnames_cal_nad), dtype=np.float64)
            for i in range(jday_cal_nad.size):
                dtime0_s = os.path.basename(fnames_cal_nad[i]).split('|')[2].split('_')[0]
                dtime0 = datetime.datetime.strptime(dtime0_s, '%Y-%m-%d')
                jday_cal_nad[i] = ssfr.util.dtime_to_jday(dtime0) + i/86400.0
            fname_cal_nad = fnames_cal_nad[np.argmin(np.abs(jday_cal_nad-jday_today))]
            data_cal_nad = ssfr.util.load_h5(fname_cal_nad)

            msg = '\nMessage [cdata_ssfr_v1]: Using <%s> for %s nadir irradiance ...' % (os.path.basename(fname_cal_nad), which_ssfr.upper())
            print(msg)
            #╰──────────────────────────────────────────────────────────────╯#
        else:
            # radiance (scale the data to 0 - 2.0 for now,
            # later we will apply radiometric response after mission to retrieve spectral RADIANCE)

            factor_zen = (np.nanmax(cnt_zen)-np.nanmin(cnt_zen)) / 2.0
            data_cal_zen = {
                    'sec_resp': np.repeat(factor_zen, wvl_zen.size)
                    }

            msg = '\nMessage [cdata_ssfr_v1]: Using [0, 2.0] scaling for %s zenith radiance ...' % (which_ssfr.upper())
            print(msg)

            factor_nad = (np.nanmax(cnt_nad)-np.nanmin(cnt_nad)) / 2.0
            data_cal_nad = {
                    'sec_resp': np.repeat(factor_nad, wvl_nad.size)
                    }

            msg = '\nMessage [cdata_ssfr_v1]: Using [0, 2.0] scaling for %s nadir radiance ...' % (which_ssfr.upper())
            print(msg)

        logic_dset = (dset_num == idset)

    return fname_h5

def ssfr_rad_cal(
        fdir_pri,
        fdir_tra,
        fdir_sec=None,
        spec_reverse=False,
        ):

    # get calibration files of primary
    #╭────────────────────────────────────────────────────────────────────────────╮#
    tags_pri = os.path.basename(fdir_pri).split('_')
    fnames_pri_ = sorted(glob.glob('%s/*.SKS' % (fdir_pri)))
    fnames_pri = [fnames_pri_[-1]]
    if len(fnames_pri) > 1:
        msg = '\nWarning [rad_cal]: find more than one file for "%s", selected "%s" ...' % (fdir_pri, fnames_pri[0])
        warnings.warn(msg)
    #╰────────────────────────────────────────────────────────────────────────────╯#


    # get calibration files of transfer
    #╭────────────────────────────────────────────────────────────────────────────╮#
    tags_tra = os.path.basename(fdir_tra).split('_')
    fnames_tra_ = sorted(glob.glob('%s/*.SKS' % (fdir_tra)))
    fnames_tra = [fnames_tra_[-1]]
    if len(fnames_tra) > 1:
        msg = '\nWarning [rad_cal]: find more than one file for "%s", selected "%s" ...' % (fdir_tra, fnames_tra[0])
        warnings.warn(msg)
    #╰────────────────────────────────────────────────────────────────────────────╯#


    # secondary calibration files from field
    #╭────────────────────────────────────────────────────────────────────────────╮#
    if fdir_sec is None:
        fdir_sec = fdir_tra
    tags_sec = os.path.basename(fdir_sec).split('_')
    fnames_sec_ = sorted(glob.glob('%s/*.SKS' % (fdir_sec)))
    fnames_sec = [fnames_sec_[-1]]
    if len(fnames_sec) > 1:
        msg = '\nWarning [rad_cal]: find more than one file for "%s", selected "%s" ...' % (fdir_sec, fnames_sec[0])
        warnings.warn(msg)
    #╰────────────────────────────────────────────────────────────────────────────╯#


    # tags
    #╭────────────────────────────────────────────────────────────────────────────╮#
    if (tags_pri[1]==tags_tra[1]) and (tags_tra[1]==tags_sec[1]):
        ssfr_tag = tags_pri[1]
    if (tags_pri[2]==tags_tra[2]) and (tags_tra[2]==tags_sec[2]):
        lc_tag = tags_pri[2]
    #╰────────────────────────────────────────────────────────────────────────────╯#

    date_today_s = datetime.datetime.now().strftime('%Y-%m-%d')

    ssfr_ = ssfr.lasp_ssfr.read_ssfr(fnames_pri, verbose=False)

    for i in range(ssfr_.Ndset):
        dset_tag = 'dset%d' % i
        int_time = ssfr_.dset_info[dset_tag]

        if len(tags_pri) == 7:
            cal_tag = '%s_%s' % (tags_pri[0], tags_pri[4])
        elif len(tags_pri) == 8:
            cal_tag = '%s_%s_%s' % (tags_pri[0], tags_pri[4], tags_pri[7])

        if len(tags_tra) == 7:
            cal_tag = '%s|%s_%s' % (cal_tag, tags_tra[0], tags_tra[4])
        elif len(tags_tra) == 8:
            cal_tag = '%s|%s_%s_%s' % (cal_tag, tags_tra[0], tags_tra[4], tags_tra[7])

        if len(tags_sec) == 7:
            cal_tag = '%s|%s_%s' % (cal_tag, tags_sec[0], tags_sec[4])
        elif len(tags_sec) == 8:
            cal_tag = '%s|%s_%s_%s' % (cal_tag, tags_sec[0], tags_sec[4], tags_sec[7])

        filename_tag = '%s|%s_processed-for-arcsix' % (cal_tag, date_today_s)

        ssfr.cal.cdata_rad_resp(fnames_pri=fnames_pri, fnames_tra=fnames_tra, fnames_sec=fnames_sec, which_ssfr='lasp|%s' % ssfr_tag, which_lc=lc_tag, int_time=int_time, which_lamp=tags_pri[4], filename_tag=filename_tag, verbose=True, spec_reverse=spec_reverse)
#╰────────────────────────────────────────────────────────────────────────────╯#



def main_ssfr_rad_cal(
        which_ssfr='lasp|ssfr-a',
        ):

    """
    Notes:
        irradiance setup:
            SSFR-A (Alvin)
              - zenith: LC4 + black plastic cased fiber
              - nadir : LC6 + stainless steel cased fiber

        irradiance backup setup:
            SSFR-B (Belana)
              - zenith: LC4 + black plastic cased fiber
              - nadir : LC6 + stainless steel cased fiber

    Available options for primary calibrations (pre-mission):
        data/arcsix/cal/rad-cal/2023-11-16_SSFR-A_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2023-11-16_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-20_SSFR-A_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-20_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-27_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350_restart

        data/arcsix/cal/rad-cal/2024-03-25_SSFR-A_nad-lc6_pri-cal_lamp-506_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_pri-cal_lamp-506_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_pri-cal_lamp-506_si-080-120_in-250-350

        data/arcsix/cal/rad-cal/2023-11-16_SSFR-B_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2023-11-16_SSFR-B_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-27_SSFR-B_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350

        data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350_postdeployment0
        data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350_postdeployment
        data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350_postdeployment

    Available options for transfer (pre-mission):
        data/arcsix/cal/rad-cal/2024-03-20_SSFR-A_nad-lc6_transfer_lamp-150c_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-20_SSFR-A_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_transfer_lamp-150c_si-080-120_in-250-350_after-pri
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350_after-pri

        data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_nad-lc6_transfer_lamp-150c_si-080-160_in-250-350
        data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350

        data/arcsix/cal/rad-cal/2024-03-25_SSFR-A_nad-lc6_transfer_lamp-150e_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-26_SSFR-A_zen-lc4_transfer_lamp-150e_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_transfer_lamp-150e_si-080-120_in-250-350_after-pri
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_transfer_lamp-150e_si-080-120_in-250-350_before-pri
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_transfer_lamp-150e_si-080-120_in-250-350_fiber-zen
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_transfer_lamp-150e_si-080-120_in-250-350_spec-zen
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150e_si-080-120_in-250-350_after-pri
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150e_si-080-120_in-250-350_before-pri
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150e_si-080-120_in-250-350_fiber-nad
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150e_si-080-120_in-250-350_restart
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150e_si-080-120_in-250-350_spec-nad

        data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_nad-lc6_transfer_lamp-150c_si-080-120_in-250-350_postdeployment
        data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350_postdeployment

    Avaiable options for secondary calibrations (or known as field calibrations):
        data/arcsix/cal/rad-cal/2024-05-26_SSFR-A_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-05-27_SSFR-A_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-06-02_SSFR-A_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-06-02_SSFR-A_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-06-09_SSFR-A_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-06-09_SSFR-A_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik

        data/arcsix/cal/rad-cal/2024-06-02_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-06-02_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-07-23_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-07-26_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-07-31_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-07-31_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-08-04_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-08-04_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-08-05_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik # after disassembly
        data/arcsix/cal/rad-cal/2024-08-10_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-08-10_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik1
        data/arcsix/cal/rad-cal/2024-08-10_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik2 # after disassembly

    fdirs = [
            {'zen': '',
             'nad': ''},
            ]
    """

    # radiometric calibration
    #╭────────────────────────────────────────────────────────────────────────────╮#
    fdir_cal = '%s/rad-cal' % _FDIR_CAL_

    # primary calibrations (pre-mission)
    #╭──────────────────────────────────────────────────────────────╮#
    # fdirs_pri_cal = ssfr.util.get_all_folders(fdir_cal, pattern='*pri-cal_lamp-1324*si-080-120*in-250-350*')
    # fdirs_pri_cal = ssfr.util.get_all_folders(fdir_cal, pattern='*pri-cal_lamp-506*si-080-120*in-250-350*')
    # for fdir_pri in fdirs_pri_cal:
    #     print(fdir_pri)
    #╰──────────────────────────────────────────────────────────────╯#

    # transfer (pre-mission)
    #╭──────────────────────────────────────────────────────────────╮#
    # fdirs_transfer = ssfr.util.get_all_folders(fdir_cal, pattern='*transfer_lamp-150c*si-080-120*in-250-350*')
    # fdirs_transfer = ssfr.util.get_all_folders(fdir_cal, pattern='*transfer_lamp-150e*si-080-120*in-250-350*')
    # for fdir_transfer in fdirs_transfer:
    #     print(fdir_transfer)
    #╰──────────────────────────────────────────────────────────────╯#

    # secondary calibrations (in-field)
    #╭──────────────────────────────────────────────────────────────╮#
    # fdirs_sec_cal = ssfr.util.get_all_folders(fdir_cal, pattern='*sec-cal_lamp-150c*si-080-120*in-250-350*')
    # fdirs_sec_cal = ssfr.util.get_all_folders(fdir_cal, pattern='*sec-cal_lamp-150e*si-080-120*in-250-350*')
    # for fdir_sec_cal in fdirs_sec_cal:
    #     print(fdir_sec_cal)
    #╰──────────────────────────────────────────────────────────────╯#
    #╰────────────────────────────────────────────────────────────────────────────╯#

    if 'ssfr-a' in which_ssfr.lower():

        # SSFR-A (regular setup for measuring irradiance)
        #╭────────────────────────────────────────────────────────────────────────────╮#
        fdirs_pri = [
                {'zen': 'data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350',
                 'nad': 'data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350'},
                # {'zen': 'data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350_post0',
                #  'nad': 'data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350_post'},
                ]

        fdirs_tra = [
                {'zen': 'data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350_after-pri',
                 'nad': 'data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_transfer_lamp-150c_si-080-120_in-250-350_after-pri'},
                # {'zen': 'data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350_post',
                #  'nad': 'data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_nad-lc6_transfer_lamp-150c_si-080-120_in-250-350_post'},
                ]

        fdirs_sec = [
                # {'zen': 'data/arcsix/cal/rad-cal/2024-05-27_SSFR-A_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                #  'nad': 'data/arcsix/cal/rad-cal/2024-05-26_SSFR-A_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                {'zen': 'data/arcsix/cal/rad-cal/2024-06-02_SSFR-A_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                 'nad': 'data/arcsix/cal/rad-cal/2024-06-02_SSFR-A_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                # {'zen': 'data/arcsix/cal/rad-cal/2024-06-09_SSFR-A_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                #  'nad': 'data/arcsix/cal/rad-cal/2024-06-09_SSFR-A_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                ]
        #╰────────────────────────────────────────────────────────────────────────────╯#

    elif 'ssfr-b' in which_ssfr.lower():


        # SSFR-B (backup setup for measuring irradiance)
        #╭────────────────────────────────────────────────────────────────────────────╮#
        fdirs_pri = [
                {'zen': 'data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350',
                 'nad': 'data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350'},
                # {'zen': 'data/arcsix/cal/rad-cal/2025-02-25_SSFR-B_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350_post',
                #  'nad': 'data/arcsix/cal/rad-cal/2025-02-25_SSFR-B_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350_post'},
                ]

        fdirs_tra = [
                {'zen': 'data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350',
                 'nad': 'data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_nad-lc6_transfer_lamp-150c_si-080-160_in-250-350'},
                # {'zen': 'data/arcsix/cal/rad-cal/2025-02-25_SSFR-B_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350_post',
                #  'nad': 'data/arcsix/cal/rad-cal/2025-02-25_SSFR-B_nad-lc6_transfer_lamp-150c_si-080-120_in-250-350_post'},
                ]

        fdirs_sec = [
                # {'nad': 'data/arcsix/cal/rad-cal/2024-06-02_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                #  'zen': 'data/arcsix/cal/rad-cal/2024-06-02_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                # {'nad': 'data/arcsix/cal/rad-cal/2024-07-23_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                #  'zen': 'data/arcsix/cal/rad-cal/2024-07-26_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                # {'nad': 'data/arcsix/cal/rad-cal/2024-07-31_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                #  'zen': 'data/arcsix/cal/rad-cal/2024-07-31_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                # {'nad': 'data/arcsix/cal/rad-cal/2024-08-04_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                #  'zen': 'data/arcsix/cal/rad-cal/2024-08-04_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                # {'nad': 'data/arcsix/cal/rad-cal/2024-08-04_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                #  'zen': 'data/arcsix/cal/rad-cal/2024-08-05_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                # {'nad': 'data/arcsix/cal/rad-cal/2024-08-10_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                #  'zen': 'data/arcsix/cal/rad-cal/2024-08-10_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik1'},
                {'nad': 'data/arcsix/cal/rad-cal/2024-08-10_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                 'zen': 'data/arcsix/cal/rad-cal/2024-08-10_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik2'},
                ]
        #╰────────────────────────────────────────────────────────────────────────────╯#

    for fdir_pri in fdirs_pri:
        for fdir_tra in fdirs_tra:
            for fdir_sec in fdirs_sec:
                for spec_tag in fdir_sec.keys():
                    fdir_pri0 = fdir_pri[spec_tag]
                    fdir_tra0 = fdir_tra[spec_tag]
                    fdir_sec0 = fdir_sec[spec_tag]

                    print(spec_tag)
                    print(fdir_pri0)
                    print(fdir_tra0)
                    print(fdir_sec0)
                    ssfr_rad_cal(fdir_pri0, fdir_tra0, fdir_sec=fdir_sec0, spec_reverse=False)
    return

def field_calibration_check(
        ssfr_tag='ssfr-a',
        lc_tag='zen',
        int_time={'si':80.0, 'in':250.0},
        ):


    tag = '%s|%s|si-%3.3d|in-%3.3d' % (ssfr_tag, lc_tag, int_time['si'], int_time['in'])

    # for post-mission
    # fnames = sorted(glob.glob('*lamp-1324_post|*pituffik*%s*.h5' % tag))

    # for pre-mission
    fnames = sorted(glob.glob('*lamp-1324|*pituffik*%s*.h5' % tag))

    # for SSFR-A post-mission azimuth sensitivity study
    # fnames = sorted(glob.glob('*lamp-1324_post0|*pituffik*%s*.h5' % tag))

    print(fnames)

    # colors = plt.cm.jet(np.linspace(0.0, 1.0, len(fnames)))

    # figure
    #/----------------------------------------------------------------------------\#
    if True:
        plt.close('all')
        fig = plt.figure(figsize=(16, 8))

        ax1 = fig.add_subplot(111)

        for i, fname in enumerate(fnames):
            tags = os.path.basename(fname).replace('.h5', '').split('|')
            f = h5py.File(fname, 'r')
            wvl = f['wvl'][...]
            sec_resp = f['sec_resp'][...]
            pri_resp = f['pri_resp'][...]
            f.close()

            if i == 0:
                ax1.plot(wvl, pri_resp, marker='o', markersize=2, lw=0.5, label='%s (Primary)' % tags[0])

            ax1.plot(wvl, sec_resp, marker='o', markersize=2, lw=0.5, label='%s (Secondary)' % tags[2])

        ax1.set_title('%s (%s)' % (ssfr_tag.upper(), lc_tag.upper()))
        ax1.set_xlabel('Wavelength [nm]')
        ax1.set_ylabel('Irradiance [$W m^{-2} nm^{-1}$]')
        ax1.set_xlim((200, 2400))
        if lc_tag == 'zen':
            ax1.set_ylim((0, 600))
        else:
            ax1.set_ylim((0, 800))
        plt.legend(fontsize=12)
        # fig.suptitle('Field Calibration (%s|%s|%s|%s)' % (ssfr_tag.upper(), lc_tag.upper(), tags[-2].upper(), tags[-1].upper()), fontsize=24)


        # save figure
        #/--------------------------------------------------------------\#
        fig.subplots_adjust(hspace=0.3, wspace=0.3)
        _metadata = {'Computer': os.uname()[1], 'Script': os.path.abspath(__file__), 'Function':sys._getframe().f_code.co_name, 'Date':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        # fig.savefig('%s_%s_%s_%s_%s.png' % (_metadata['Function'], ssfr_tag, lc_tag, tags[-2], tags[-1]), bbox_inches='tight', metadata=_metadata)
        fig.savefig('%s_%s_%s.png' % (_metadata['Function'], ssfr_tag, lc_tag), bbox_inches='tight', metadata=_metadata)
        #\--------------------------------------------------------------/#
    #\----------------------------------------------------------------------------/#



def main_ssfr_rad_cal_all(
        which_ssfr='lasp|ssfr-a',
        ):

    """
    Notes:
        irradiance setup:
            SSFR-A (Alvin)
              - zenith: LC4 + black plastic cased fiber
              - nadir : LC6 + stainless steel cased fiber

        irradiance backup setup:
            SSFR-B (Belana)
              - zenith: LC4 + black plastic cased fiber
              - nadir : LC6 + stainless steel cased fiber

    Available options for primary calibrations (pre-mission):
        data/arcsix/cal/rad-cal/2023-11-16_SSFR-A_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2023-11-16_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-20_SSFR-A_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-20_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-27_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350_restart

        data/arcsix/cal/rad-cal/2024-03-25_SSFR-A_nad-lc6_pri-cal_lamp-506_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_pri-cal_lamp-506_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_pri-cal_lamp-506_si-080-120_in-250-350

        data/arcsix/cal/rad-cal/2023-11-16_SSFR-B_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2023-11-16_SSFR-B_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-27_SSFR-B_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350

        data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350_postdeployment0
        data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350_postdeployment
        data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350_postdeployment

    Available options for transfer (pre-mission):
        data/arcsix/cal/rad-cal/2024-03-20_SSFR-A_nad-lc6_transfer_lamp-150c_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-20_SSFR-A_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_transfer_lamp-150c_si-080-120_in-250-350_after-pri
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350_after-pri

        data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_nad-lc6_transfer_lamp-150c_si-080-160_in-250-350
        data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350

        data/arcsix/cal/rad-cal/2024-03-25_SSFR-A_nad-lc6_transfer_lamp-150e_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-26_SSFR-A_zen-lc4_transfer_lamp-150e_si-080-120_in-250-350
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_transfer_lamp-150e_si-080-120_in-250-350_after-pri
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_transfer_lamp-150e_si-080-120_in-250-350_before-pri
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_transfer_lamp-150e_si-080-120_in-250-350_fiber-zen
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_transfer_lamp-150e_si-080-120_in-250-350_spec-zen
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150e_si-080-120_in-250-350_after-pri
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150e_si-080-120_in-250-350_before-pri
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150e_si-080-120_in-250-350_fiber-nad
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150e_si-080-120_in-250-350_restart
        data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150e_si-080-120_in-250-350_spec-nad

        data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_nad-lc6_transfer_lamp-150c_si-080-120_in-250-350_postdeployment
        data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350_postdeployment

    Avaiable options for secondary calibrations (or known as field calibrations):
        data/arcsix/cal/rad-cal/2024-05-26_SSFR-A_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-05-27_SSFR-A_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-06-02_SSFR-A_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-06-02_SSFR-A_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-06-09_SSFR-A_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-06-09_SSFR-A_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik

        data/arcsix/cal/rad-cal/2024-06-02_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-06-02_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-07-23_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-07-26_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-07-31_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-07-31_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-08-04_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-08-04_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-08-05_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik # after disassembly
        data/arcsix/cal/rad-cal/2024-08-10_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik
        data/arcsix/cal/rad-cal/2024-08-10_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik1
        data/arcsix/cal/rad-cal/2024-08-10_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik2 # after disassembly

    fdirs = [
            {'zen': '',
             'nad': ''},
            ]
    """

    # radiometric calibration
    #╭────────────────────────────────────────────────────────────────────────────╮#
    fdir_cal = '%s/rad-cal' % _FDIR_CAL_

    # primary calibrations (pre-mission)
    #╭──────────────────────────────────────────────────────────────╮#
    # fdirs_pri_cal = ssfr.util.get_all_folders(fdir_cal, pattern='*pri-cal_lamp-1324*si-080-120*in-250-350*')
    # fdirs_pri_cal = ssfr.util.get_all_folders(fdir_cal, pattern='*pri-cal_lamp-506*si-080-120*in-250-350*')
    # for fdir_pri in fdirs_pri_cal:
    #     print(fdir_pri)
    #╰──────────────────────────────────────────────────────────────╯#

    # transfer (pre-mission)
    #╭──────────────────────────────────────────────────────────────╮#
    # fdirs_transfer = ssfr.util.get_all_folders(fdir_cal, pattern='*transfer_lamp-150c*si-080-120*in-250-350*')
    # fdirs_transfer = ssfr.util.get_all_folders(fdir_cal, pattern='*transfer_lamp-150e*si-080-120*in-250-350*')
    # for fdir_transfer in fdirs_transfer:
    #     print(fdir_transfer)
    #╰──────────────────────────────────────────────────────────────╯#

    # secondary calibrations (in-field)
    #╭──────────────────────────────────────────────────────────────╮#
    # fdirs_sec_cal = ssfr.util.get_all_folders(fdir_cal, pattern='*sec-cal_lamp-150c*si-080-120*in-250-350*')
    # fdirs_sec_cal = ssfr.util.get_all_folders(fdir_cal, pattern='*sec-cal_lamp-150e*si-080-120*in-250-350*')
    # for fdir_sec_cal in fdirs_sec_cal:
    #     print(fdir_sec_cal)
    #╰──────────────────────────────────────────────────────────────╯#
    #╰────────────────────────────────────────────────────────────────────────────╯#

    if 'ssfr-a' in which_ssfr.lower():

        # SSFR-A (regular setup for measuring irradiance)
        #╭────────────────────────────────────────────────────────────────────────────╮#
        fdirs_pri = [
                {'zen': 'data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350',
                 'nad': 'data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350'},
                # {'zen': 'data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350_post0',
                #  'nad': 'data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350_post'},
                ]

        fdirs_tra = [
                {'zen': 'data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350_after-pri',
                 'nad': 'data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_transfer_lamp-150c_si-080-120_in-250-350_after-pri'},
                # {'zen': 'data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350_post',
                #  'nad': 'data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_nad-lc6_transfer_lamp-150c_si-080-120_in-250-350_post'},
                ]

        fdirs_sec = [
                {'zen': 'data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350_after-pri',
                 'nad': 'data/arcsix/cal/rad-cal/2024-03-29_SSFR-A_nad-lc6_transfer_lamp-150c_si-080-120_in-250-350_after-pri'},
                {'zen': 'data/arcsix/cal/rad-cal/2024-05-27_SSFR-A_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                 'nad': 'data/arcsix/cal/rad-cal/2024-05-26_SSFR-A_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                {'zen': 'data/arcsix/cal/rad-cal/2024-06-02_SSFR-A_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                 'nad': 'data/arcsix/cal/rad-cal/2024-06-02_SSFR-A_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                {'zen': 'data/arcsix/cal/rad-cal/2024-06-09_SSFR-A_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                 'nad': 'data/arcsix/cal/rad-cal/2024-06-09_SSFR-A_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                {'zen': 'data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350_post',
                 'nad': 'data/arcsix/cal/rad-cal/2025-02-18_SSFR-A_nad-lc6_transfer_lamp-150c_si-080-120_in-250-350_post'},
                ]
        #╰────────────────────────────────────────────────────────────────────────────╯#

    elif 'ssfr-b' in which_ssfr.lower():


        # SSFR-B (backup setup for measuring irradiance)
        #╭────────────────────────────────────────────────────────────────────────────╮#
        fdirs_pri = [
                {'zen': 'data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350',
                 'nad': 'data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350'},
                # {'zen': 'data/arcsix/cal/rad-cal/2025-02-25_SSFR-B_zen-lc4_pri-cal_lamp-1324_si-080-120_in-250-350_post',
                #  'nad': 'data/arcsix/cal/rad-cal/2025-02-25_SSFR-B_nad-lc6_pri-cal_lamp-1324_si-080-120_in-250-350_post'},
                ]

        fdirs_tra = [
                {'zen': 'data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350',
                 'nad': 'data/arcsix/cal/rad-cal/2024-03-21_SSFR-B_nad-lc6_transfer_lamp-150c_si-080-160_in-250-350'},
                # {'zen': 'data/arcsix/cal/rad-cal/2025-02-25_SSFR-B_zen-lc4_transfer_lamp-150c_si-080-120_in-250-350_post',
                #  'nad': 'data/arcsix/cal/rad-cal/2025-02-25_SSFR-B_nad-lc6_transfer_lamp-150c_si-080-120_in-250-350_post'},
                ]

        fdirs_sec = [
                # {'nad': 'data/arcsix/cal/rad-cal/2024-06-02_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                #  'zen': 'data/arcsix/cal/rad-cal/2024-06-02_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                # {'nad': 'data/arcsix/cal/rad-cal/2024-07-23_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                #  'zen': 'data/arcsix/cal/rad-cal/2024-07-26_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                # {'nad': 'data/arcsix/cal/rad-cal/2024-07-31_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                #  'zen': 'data/arcsix/cal/rad-cal/2024-07-31_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                # {'nad': 'data/arcsix/cal/rad-cal/2024-08-04_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                #  'zen': 'data/arcsix/cal/rad-cal/2024-08-04_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                # {'nad': 'data/arcsix/cal/rad-cal/2024-08-04_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                #  'zen': 'data/arcsix/cal/rad-cal/2024-08-05_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik'},
                # {'nad': 'data/arcsix/cal/rad-cal/2024-08-10_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                #  'zen': 'data/arcsix/cal/rad-cal/2024-08-10_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik1'},
                {'nad': 'data/arcsix/cal/rad-cal/2024-08-10_SSFR-B_nad-lc6_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik',
                 'zen': 'data/arcsix/cal/rad-cal/2024-08-10_SSFR-B_zen-lc4_sec-cal_lamp-150c_si-080-120_in-250-350_pituffik2'},
                ]
        #╰────────────────────────────────────────────────────────────────────────────╯#

    for fdir_pri in fdirs_pri:
        for fdir_tra in fdirs_tra:
            for fdir_sec in fdirs_sec:
                for spec_tag in fdir_sec.keys():
                    fdir_pri0 = fdir_pri[spec_tag]
                    fdir_tra0 = fdir_tra[spec_tag]
                    fdir_sec0 = fdir_sec[spec_tag]

                    print(spec_tag)
                    print(fdir_pri0)
                    print(fdir_tra0)
                    print(fdir_sec0)
                    ssfr_rad_cal(fdir_pri0, fdir_tra0, fdir_sec=fdir_sec0, spec_reverse=False)
    return

if __name__ == '__main__':

    # process field calibration (SSFR-A)
    #╭────────────────────────────────────────────────────────────────────────────╮#
    # main_ssfr_rad_cal(which_ssfr='lasp|ssfr-a')

    # for lc_tag in ['zen', 'nad']:
    #     for int_time in [{'si':80, 'in':250}, {'si':120, 'in':350}]:
    #         field_calibration_check(lc_tag=lc_tag, int_time=int_time)
    #╰────────────────────────────────────────────────────────────────────────────╯#

    # process field calibration (SSFR-B)
    #╭────────────────────────────────────────────────────────────────────────────╮#
    # main_ssfr_rad_cal(which_ssfr='lasp|ssfr-b')

    # for lc_tag in ['zen', 'nad']:
    #     for int_time in [{'si':80, 'in':250}, {'si':120, 'in':350}]:
    #         field_calibration_check(ssfr_tag='ssfr-b', lc_tag=lc_tag, int_time=int_time)
    #╰────────────────────────────────────────────────────────────────────────────╯#

    main_ssfr_rad_cal_all(which_ssfr='lasp|ssfr-a')
    pass
