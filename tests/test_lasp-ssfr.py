import os
import sys
import glob
import datetime
import h5py
import numpy as np
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
mpl.use('Agg')


import ssfr


_mission_   = 'arcsix'
_spns_      = 'spns-b'
_ssfr_      = 'ssfr-b'
_fdir_data_ = 'data/%s/pre-mission' % _mission_
_fdir_hsk_  = '%s/raw/hsk'
_fdir_ssfr_ = '%s/raw/%s' % (_fdir_data_, _ssfr_)
_fdir_spns_ = '%s/raw/%s' % (_fdir_data_, _spns_)
_fdir_v0_   = 'data/processed'
_fdir_v1_   = 'data/processed'
_fdir_v2_   = 'data/processed'



def test_joint_wvl_cal(ssfr_tag, lc_tag, lamp_tag, Nchan=256):


    # si and in tags
    #/----------------------------------------------------------------------------\#
    si_tag = '%s|si' % lc_tag
    in_tag = '%s|in' % lc_tag
    #\----------------------------------------------------------------------------/#

    # si and in index
    #/----------------------------------------------------------------------------\#
    indices_spec = {
            'zen|si': 0,
            'zen|in': 1,
            'nad|si': 2,
            'nad|in': 3,
            }
    index_si = indices_spec[si_tag]
    index_in = indices_spec[in_tag]
    #\----------------------------------------------------------------------------/#

    # get wavelength
    #/----------------------------------------------------------------------------\#
    wvls = ssfr.lasp_ssfr.get_ssfr_wvl('lasp|%s' % ssfr_tag.lower())
    wvl_si = wvls[si_tag]
    wvl_in = wvls[in_tag]
    #\----------------------------------------------------------------------------/#

    # get spectra counts data
    #/----------------------------------------------------------------------------\#
    fdir_data = '/argus/field/arcsix/cal/rad-cal'
    fdir   =  sorted(glob.glob('%s/*%s*%s*%s*' % (fdir_data, ssfr_tag, lc_tag, lamp_tag)))[0]
    fnames = sorted(glob.glob('%s/*00001.SKS' % (fdir)))
    ssfr_data = ssfr.lasp_ssfr.read_ssfr(fnames)

    cnt_si_dset0 = ssfr_data.dset0['spectra_dark-corr'][:, :, index_si]/ssfr_data.dset0['info']['int_time'][si_tag]
    cnt_in_dset0 = ssfr_data.dset0['spectra_dark-corr'][:, :, index_in]/ssfr_data.dset0['info']['int_time'][in_tag]

    cnt_si_dset1 = ssfr_data.dset1['spectra_dark-corr'][:, :, index_si]/ssfr_data.dset1['info']['int_time'][si_tag]
    cnt_in_dset1 = ssfr_data.dset1['spectra_dark-corr'][:, :, index_in]/ssfr_data.dset1['info']['int_time'][in_tag]
    #\----------------------------------------------------------------------------/#

    # get response
    #/----------------------------------------------------------------------------\#
    dset_s = 'dset0'
    fnames_cal_dset0 = sorted(glob.glob('%s/cal/*cal-rad-pri|lasp|%s|%s|%s*.h5' % (ssfr.common.fdir_data, ssfr_tag.lower(), lc_tag.lower(), dset_s.lower())))
    f = h5py.File(fnames_cal_dset0[-1], 'r')
    resp_si_dset0 = f[si_tag][...]
    resp_in_dset0 = f[in_tag][...]
    f.close()

    dset_s = 'dset1'
    fnames_cal_dset1 = sorted(glob.glob('%s/cal/*cal-rad-pri|lasp|%s|%s|%s*.h5' % (ssfr.common.fdir_data, ssfr_tag.lower(), lc_tag.lower(), dset_s.lower())))
    f = h5py.File(fnames_cal_dset1[-1], 'r')
    resp_si_dset1 = f[si_tag][...]
    resp_in_dset1 = f[in_tag][...]
    f.close()
    #\----------------------------------------------------------------------------/#


    # get flux
    #/----------------------------------------------------------------------------\#
    flux_si_dset0 = cnt_si_dset0 / resp_si_dset0
    flux_in_dset0 = cnt_in_dset0 / resp_in_dset0
    flux_si_dset1 = cnt_si_dset1 / resp_si_dset1
    flux_in_dset1 = cnt_in_dset1 / resp_in_dset1
    #\----------------------------------------------------------------------------/#


    wvl_joint = 950.0
    x = np.arange(flux_si_dset0.shape[0])

    index_joint_si = np.where(wvl_si< wvl_joint)[0][-1]
    index_joint_in = np.where(wvl_in>=wvl_joint)[0][-1]

    # figure
    #/----------------------------------------------------------------------------\#
    for index in np.arange(30, 91):
        plt.close('all')
        fig = plt.figure(figsize=(12, 12))
        fig.suptitle('LASP|%s|%s %5.5d' % (ssfr_tag.upper(), lc_tag.upper(), index))
        # plot
        #/--------------------------------------------------------------\#
        ax1 = fig.add_subplot(312)
        ax1.scatter(wvl_si, flux_si_dset0[index, :], s=6, c='r'      , lw=0.0, alpha=0.5)
        ax1.scatter(wvl_si, flux_si_dset1[index, :], s=6, c='magenta', lw=0.0, alpha=0.5)
        ax1.scatter(wvl_in, flux_in_dset0[index, :], s=6, c='b'      , lw=0.0, alpha=0.5)
        ax1.scatter(wvl_in, flux_in_dset1[index, :], s=6, c='cyan'   , lw=0.0, alpha=0.5)

        ax1.scatter(wvl_si[index_joint_si], flux_si_dset0[index, index_joint_si], s=250, c='r', lw=0.0, marker='*')
        ax1.scatter(wvl_si[index_joint_si], flux_si_dset1[index, index_joint_si], s=250, c='magenta', lw=0.0, marker='*')
        ax1.scatter(wvl_in[index_joint_in], flux_in_dset0[index, index_joint_in], s=250, c='b', lw=0.0, marker='*')
        ax1.scatter(wvl_in[index_joint_in], flux_in_dset1[index, index_joint_in], s=250, c='cyan', lw=0.0, marker='*')

        ax1.axvline(wvl_joint, color='gray', lw=1.5, ls='--')
        ax1.axvspan(750, 1150, color='gray', alpha=0.1, lw=0.0)
        ax1.set_ylabel('Irradiance [$\mathrm{W m^{-2} nm^{-1}}$]')
        ax1.set_xlabel('Wavelength [nm]')
        ax1.set_ylim((0.0, 0.3))
        ax1.set_title('Spectra')

        ax2 = fig.add_subplot(313)
        ax2.scatter(wvl_si, flux_si_dset0[index, :], s=6, c='r'      , lw=0.0, alpha=0.5)
        ax2.scatter(wvl_si, flux_si_dset1[index, :], s=6, c='magenta', lw=0.0, alpha=0.5)
        ax2.scatter(wvl_in, flux_in_dset0[index, :], s=6, c='b'      , lw=0.0, alpha=0.5)
        ax2.scatter(wvl_in, flux_in_dset1[index, :], s=6, c='cyan'   , lw=0.0, alpha=0.5)

        ax2.scatter(wvl_si[index_joint_si], flux_si_dset0[index, index_joint_si], s=250, c='r', lw=0.0, marker='*')
        ax2.scatter(wvl_si[index_joint_si], flux_si_dset1[index, index_joint_si], s=250, c='magenta', lw=0.0, marker='*')
        ax2.scatter(wvl_in[index_joint_in], flux_in_dset0[index, index_joint_in], s=250, c='b', lw=0.0, marker='*')
        ax2.scatter(wvl_in[index_joint_in], flux_in_dset1[index, index_joint_in], s=250, c='cyan', lw=0.0, marker='*')

        ax2.axvline(wvl_joint, color='gray', lw=1.5, ls='--')
        ax2.set_ylabel('Irradiance [$\mathrm{W m^{-2} nm^{-1}}$]')
        ax2.set_xlabel('Wavelength [nm]')
        ax2.set_xlim((750, 1150))
        ax2.set_ylim((0.18, 0.26))
        ax2.set_title('Spectra [Zoomed In]')


        ax3 = fig.add_subplot(311)
        ax3.plot(x, flux_si_dset0[:, index_joint_si], lw=2, c='r'      , alpha=0.5, marker='o', markersize=1)
        ax3.plot(x, flux_si_dset1[:, index_joint_si], lw=2, c='magenta', alpha=0.5, marker='o', markersize=1)
        ax3.plot(x, flux_in_dset0[:, index_joint_in], lw=2, c='b'      , alpha=0.5, marker='o', markersize=1)
        ax3.plot(x, flux_in_dset1[:, index_joint_in], lw=2, c='cyan'   , alpha=0.5, marker='o', markersize=1)

        ax3.scatter(index, flux_si_dset0[index, index_joint_si], s=250, c='r', lw=0.0, marker='*')
        ax3.scatter(index, flux_si_dset1[index, index_joint_si], s=250, c='magenta', lw=0.0, marker='*')
        ax3.scatter(index, flux_in_dset0[index, index_joint_in], s=250, c='b', lw=0.0, marker='*')
        ax3.scatter(index, flux_in_dset1[index, index_joint_in], s=250, c='cyan', lw=0.0, marker='*')

        ax3.axvline(index, color='gray', lw=1.5, ls='--')
        ax3.set_ylabel('Irradiance [$\mathrm{W m^{-2} nm^{-1}}$]')
        ax3.set_xlabel('Index')
        ax3.set_ylim((0.18, 0.26))
        ax3.set_title('Time Series')
        #\--------------------------------------------------------------/#
        # save figure
        #/--------------------------------------------------------------\#
        fig.subplots_adjust(hspace=0.35, wspace=0.3)
        _metadata = {'Computer': os.uname()[1], 'Script': os.path.abspath(__file__), 'Function':sys._getframe().f_code.co_name, 'Date':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        fig.savefig('%5.5d_%s_[lasp|%s|%s].png' % (index, _metadata['Function'], ssfr_tag.lower(), lc_tag.lower()), bbox_inches='tight', metadata=_metadata)
        #\--------------------------------------------------------------/#
    #\----------------------------------------------------------------------------/#

def main_test_joint_wvl_cal():

    # radiometric calibration
    #/----------------------------------------------------------------------------\#
    for ssfr_tag in ['SSFR-A', 'SSFR-B']:
        for lc_tag in ['zen', 'nad']:
            for lamp_tag in ['1324']:
                test_joint_wvl_cal(ssfr_tag, lc_tag, lamp_tag)
    #\----------------------------------------------------------------------------/#



def test_joint_wvl_skywatch(ssfr_tag, lc_tag, date_tag, Nchan=256):

    # si and in tags
    #/----------------------------------------------------------------------------\#
    si_tag = '%s|si' % lc_tag
    in_tag = '%s|in' % lc_tag
    #\----------------------------------------------------------------------------/#

    # si and in index
    #/----------------------------------------------------------------------------\#
    indices_spec = {
            'zen|si': 0,
            'zen|in': 1,
            'nad|si': 2,
            'nad|in': 3,
            }
    index_si = indices_spec[si_tag]
    index_in = indices_spec[in_tag]
    #\----------------------------------------------------------------------------/#

    # get wavelength
    #/----------------------------------------------------------------------------\#
    wvls = ssfr.lasp_ssfr.get_ssfr_wvl('lasp|%s' % ssfr_tag.lower())
    wvl_si = wvls[si_tag]
    wvl_in = wvls[in_tag]
    #\----------------------------------------------------------------------------/#

    # get spectra counts data
    #/----------------------------------------------------------------------------\#
    fdir_data = '../examples/data/arcsix/pre-mission/raw/%s' % (ssfr_tag.lower())
    fnames = sorted(glob.glob('%s/%s/*.SKS' % (fdir_data, date_tag)))
    ssfr_data = ssfr.lasp_ssfr.read_ssfr(fnames, dark_corr_mode='interp', which_ssfr='lasp|%s' % _ssfr_.lower(), dark_extend=4, light_extend=4)

    cnt_si_dset0 = ssfr_data.dset0['spectra_dark-corr'][:, :, index_si]/ssfr_data.dset0['info']['int_time'][si_tag]
    cnt_in_dset0 = ssfr_data.dset0['spectra_dark-corr'][:, :, index_in]/ssfr_data.dset0['info']['int_time'][in_tag]

    cnt_si_dset1 = ssfr_data.dset1['spectra_dark-corr'][:, :, index_si]/ssfr_data.dset1['info']['int_time'][si_tag]
    cnt_in_dset1 = ssfr_data.dset1['spectra_dark-corr'][:, :, index_in]/ssfr_data.dset1['info']['int_time'][in_tag]
    #\----------------------------------------------------------------------------/#

    # get response
    #/----------------------------------------------------------------------------\#
    dset_s = 'dset0'
    fnames_cal_dset0 = sorted(glob.glob('%s/cal/*cal-rad-pri|lasp|%s|%s|%s*.h5' % (ssfr.common.fdir_data, ssfr_tag.lower(), lc_tag.lower(), dset_s.lower())))
    f = h5py.File(fnames_cal_dset0[-1], 'r')
    resp_si_dset0 = f[si_tag][...]
    resp_in_dset0 = f[in_tag][...]
    f.close()

    dset_s = 'dset1'
    fnames_cal_dset1 = sorted(glob.glob('%s/cal/*cal-rad-pri|lasp|%s|%s|%s*.h5' % (ssfr.common.fdir_data, ssfr_tag.lower(), lc_tag.lower(), dset_s.lower())))
    f = h5py.File(fnames_cal_dset1[-1], 'r')
    resp_si_dset1 = f[si_tag][...]
    resp_in_dset1 = f[in_tag][...]
    f.close()
    #\----------------------------------------------------------------------------/#


    # get flux
    #/----------------------------------------------------------------------------\#
    flux_si_dset0 = cnt_si_dset0 / resp_si_dset0
    flux_in_dset0 = cnt_in_dset0 / resp_in_dset0
    flux_si_dset1 = cnt_si_dset1 / resp_si_dset1
    flux_in_dset1 = cnt_in_dset1 / resp_in_dset1
    #\----------------------------------------------------------------------------/#


    wvl_joint = 950.0
    x0 = np.arange(flux_si_dset0.shape[0])
    x1 = np.arange(flux_si_dset1.shape[0])

    index_joint_si = np.where(wvl_si< wvl_joint)[0][-1]
    index_joint_in = np.where(wvl_in>=wvl_joint)[0][-1]

    # figure
    #/----------------------------------------------------------------------------\#
    for index in np.arange(0, x0.size, 60):
        plt.close('all')
        fig = plt.figure(figsize=(12, 12))
        fig.suptitle('LASP|%s|%s %s %5.5d' % (ssfr_tag.upper(), lc_tag.upper(), date_tag, index))
        # plot
        #/--------------------------------------------------------------\#
        ax1 = fig.add_subplot(312)
        ax1.scatter(wvl_si, flux_si_dset0[index, :], s=6, c='r'      , lw=0.0, alpha=0.5)
        ax1.scatter(wvl_si, flux_si_dset1[index, :], s=6, c='magenta', lw=0.0, alpha=0.5)
        ax1.scatter(wvl_in, flux_in_dset0[index, :], s=6, c='b'      , lw=0.0, alpha=0.5)
        ax1.scatter(wvl_in, flux_in_dset1[index, :], s=6, c='cyan'   , lw=0.0, alpha=0.5)

        ax1.scatter(wvl_si[index_joint_si], flux_si_dset0[index, index_joint_si], s=250, c='r', lw=0.0, marker='*')
        ax1.scatter(wvl_si[index_joint_si], flux_si_dset1[index, index_joint_si], s=250, c='magenta', lw=0.0, marker='*')
        ax1.scatter(wvl_in[index_joint_in], flux_in_dset0[index, index_joint_in], s=250, c='b', lw=0.0, marker='*')
        ax1.scatter(wvl_in[index_joint_in], flux_in_dset1[index, index_joint_in], s=250, c='cyan', lw=0.0, marker='*')

        ax1.axvline(wvl_joint, color='gray', lw=1.5, ls='--')
        ax1.axvspan(750, 1150, color='gray', alpha=0.1, lw=0.0)
        ax1.set_ylabel('Irradiance [$\mathrm{W m^{-2} nm^{-1}}$]')
        ax1.set_xlabel('Wavelength [nm]')
        ax1.set_ylim((0.0, 1.0))
        ax1.set_title('Spectra')

        ax2 = fig.add_subplot(313)
        ax2.scatter(wvl_si, flux_si_dset0[index, :], s=6, c='r'      , lw=0.0, alpha=0.5)
        ax2.scatter(wvl_si, flux_si_dset1[index, :], s=6, c='magenta', lw=0.0, alpha=0.5)
        ax2.scatter(wvl_in, flux_in_dset0[index, :], s=6, c='b'      , lw=0.0, alpha=0.5)
        ax2.scatter(wvl_in, flux_in_dset1[index, :], s=6, c='cyan'   , lw=0.0, alpha=0.5)

        ax2.scatter(wvl_si[index_joint_si], flux_si_dset0[index, index_joint_si], s=250, c='r', lw=0.0, marker='*')
        ax2.scatter(wvl_si[index_joint_si], flux_si_dset1[index, index_joint_si], s=250, c='magenta', lw=0.0, marker='*')
        ax2.scatter(wvl_in[index_joint_in], flux_in_dset0[index, index_joint_in], s=250, c='b', lw=0.0, marker='*')
        ax2.scatter(wvl_in[index_joint_in], flux_in_dset1[index, index_joint_in], s=250, c='cyan', lw=0.0, marker='*')

        ax2.axvline(wvl_joint, color='gray', lw=1.5, ls='--')
        ax2.set_ylabel('Irradiance [$\mathrm{W m^{-2} nm^{-1}}$]')
        ax2.set_xlabel('Wavelength [nm]')
        ax2.set_xlim((750, 1150))
        # ax2.set_ylim((0.18, 0.26))
        ax2.set_ylim((0.0, 0.4))
        ax2.set_title('Spectra [Zoomed In]')


        ax3 = fig.add_subplot(311)
        ax3.plot(x0, flux_si_dset0[:, index_joint_si], lw=2, c='r'      , alpha=0.5, marker='o', markersize=1)
        ax3.plot(x1, flux_si_dset1[:, index_joint_si], lw=2, c='magenta', alpha=0.5, marker='o', markersize=1)
        ax3.plot(x0, flux_in_dset0[:, index_joint_in], lw=2, c='b'      , alpha=0.5, marker='o', markersize=1)
        ax3.plot(x1, flux_in_dset1[:, index_joint_in], lw=2, c='cyan'   , alpha=0.5, marker='o', markersize=1)

        ax3.scatter(index, flux_si_dset0[index, index_joint_si], s=250, c='r', lw=0.0, marker='*')
        ax3.scatter(index, flux_si_dset1[index, index_joint_si], s=250, c='magenta', lw=0.0, marker='*')
        ax3.scatter(index, flux_in_dset0[index, index_joint_in], s=250, c='b', lw=0.0, marker='*')
        ax3.scatter(index, flux_in_dset1[index, index_joint_in], s=250, c='cyan', lw=0.0, marker='*')

        ax3.axvline(index, color='gray', lw=1.5, ls='--')
        ax3.set_ylabel('Irradiance [$\mathrm{W m^{-2} nm^{-1}}$]')
        ax3.set_xlabel('Index')
        # ax3.set_ylim((0.18, 0.26))
        ax3.set_ylim((0.0, 0.4))
        ax3.set_title('Time Series')
        #\--------------------------------------------------------------/#
        # save figure
        #/--------------------------------------------------------------\#
        fig.subplots_adjust(hspace=0.35, wspace=0.3)
        _metadata = {'Computer': os.uname()[1], 'Script': os.path.abspath(__file__), 'Function':sys._getframe().f_code.co_name, 'Date':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        fig.savefig('%5.5d_%s_%s_[lasp|%s|%s].png' % (index, date_tag, _metadata['Function'], ssfr_tag.lower(), lc_tag.lower()), bbox_inches='tight', metadata=_metadata)
        #\--------------------------------------------------------------/#
    #\----------------------------------------------------------------------------/#

def main_test_joint_wvl_skywatch():

    # skywatch
    #/----------------------------------------------------------------------------\#
    # for ssfr_tag in ['SSFR-A']:
    #     for lc_tag in ['zen', 'nad']:
    #         for date_tag in ['2023-10-27', '2023-10-30']:
    #             test_joint_wvl_skywatch(ssfr_tag, lc_tag, date_tag)
    #\----------------------------------------------------------------------------/#

    # skywatch
    #/----------------------------------------------------------------------------\#
    for ssfr_tag in ['SSFR-B']:
        # for lc_tag in ['zen', 'nad']:
        #     for date_tag in ['2023-10-19', '2023-10-20']:
        for lc_tag in ['zen']:
            for date_tag in ['2023-10-19']:
                test_joint_wvl_skywatch(ssfr_tag, lc_tag, date_tag)
    #\----------------------------------------------------------------------------/#



def test_dark_cnt():

    fdir = '../examples/data/arcsix/cal/rad-cal/SSFR-B_2023-11-16_lab-rad-cal-zen-1324'
    fnames = sorted(glob.glob('%s/*00001.SKS' % (fdir)))
    ssfr_cal = ssfr.lasp_ssfr.read_ssfr(fnames)

    wvls = ssfr.lasp_ssfr.get_ssfr_wavelength()
    print(wvls)


if __name__ == '__main__':

    # main_test_joint_wvl_cal()
    # main_test_joint_wvl_skywatch()
    test_dark_cnt()
