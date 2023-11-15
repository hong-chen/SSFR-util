import os
import sys
import datetime
import warnings
import h5py
import numpy as np
from scipy import interpolate
from scipy.io import readsav

import ssfr



__all__ = ['cal_rad_resp', 'cdata_rad_resp']



def cal_rad_resp(
        fnames,
        resp=None,
        which_ssfr='lasp|ssfr-a',
        which_lc='zen',
        which_lamp='f-1324',
        ):

    # check SSFR spectrometer
    #/----------------------------------------------------------------------------\#
    which_ssfr = which_ssfr.lower()
    which_lab  = which_ssfr.split('|')[0]
    if which_lab == 'nasa':
        import ssfr.nasa_ssfr as ssfr_toolbox
    elif which_lab == 'lasp':
        import ssfr.lasp_ssfr as ssfr_toolbox
    else:
        msg = '\nError [cal_rad_resp]: <which_ssfr=> does not support <\'%s\'> (only supports <\'nasa|ssfr-6\'> or <\'lasp|ssfr-a\'> or <\'lasp|ssfr-b\'>).' % which_ssfr
        raise ValueError(msg)
    #\----------------------------------------------------------------------------/#


    # check light collector
    #/----------------------------------------------------------------------------\#
    which_lc = which_lc.lower()
    if which_lc == 'zen':
        index_si = 0
        index_in = 1
    elif which_lc == 'nad':
        index_si = 2
        index_in = 3
    else:
        msg = '\nError [cal_rad_resp]: <which_lc=> does not support <\'%s\'> (only supports <\'zen\'> or <\'nad\'>).' % which_lc
        raise ValueError(msg)
    #\----------------------------------------------------------------------------/#


    # get radiometric response
    # by default (resp=None), this function will perform primary radiometric calibration
    #/----------------------------------------------------------------------------\#
    if resp is None:

        # check lamp
        #/----------------------------------------------------------------------------\#
        which_lamp = which_lamp.lower()
        if which_lamp[:4] == 'f-50':
            which_lamp = 'f-506c'
        #\----------------------------------------------------------------------------/#

        # read in calibrated lamp data and interpolated at SSFR wavelengths
        #/--------------------------------------------------------------\#
        fname_lamp = '%s/%s.dat' % (ssfr.common.fdir_data, which_lamp)
        if not os.path.exists(fname_lamp):
            msg = '\nError [cal_rad_resp]: Cannot locate calibration file for lamp <%s>.' % which_lamp
            raise OSError(msg)

        data      = np.loadtxt(fname_lamp)
        data_wvl  = data[:, 0]
        if which_lamp == 'f-506c':
            data_flux = data[:, 1]*0.01
        else:
            data_flux = data[:, 1]*10000.0

        # !!!!!!!!!! this will change !!!!!!!!!!!!!!
        #/----------------------------------------------------------------------------\#
        wvls = ssfr_toolbox.get_ssfr_wavelength()
        wvl_si = wvls['%s|si' % which_lc]
        wvl_in = wvls['%s|in' % which_lc]
        #\----------------------------------------------------------------------------/#

        lamp_std_si = np.zeros_like(wvl_si)
        for i in range(lamp_std_si.size):
            lamp_std_si[i] = ssfr.util.cal_weighted_flux(wvl_si[i], data_wvl, data_flux, slit_func_file='%s/vis_0.1nm_s.dat' % ssfr.common.fdir_data)

        lamp_std_in = np.zeros_like(wvl_in)
        for i in range(lamp_std_in.size):
            lamp_std_in[i] = ssfr.util.cal_weighted_flux(wvl_in[i], data_wvl, data_flux, slit_func_file='%s/nir_0.1nm_s.dat' % ssfr.common.fdir_data)

        # at this point we have (W m^-2 nm^-1 as a function of wavelength)
        resp = {'si':lamp_std_si,
                'in':lamp_std_in}
        #\--------------------------------------------------------------/#
    #\----------------------------------------------------------------------------/#

    ####### stopped here ########

    # read raw data
    #/----------------------------------------------------------------------------\#
    ssfr_l = ssfr_toolbox.read_ssfr([fnames['cal']])
    ssfr_d = ssfr_toolbox.read_ssfr([fnames['dark']])
    #\----------------------------------------------------------------------------/#


    # Silicon
    #/----------------------------------------------------------------------------\#
    counts_l  = ssfr_l.spectra[:, :, index_si]
    counts_d  = ssfr_d.spectra[:, :, index_si]

    logic_l   = (np.abs(ssfr_l.int_time[:, index_si]-int_time['si'])<0.00001) & (ssfr_l.shutter==0)
    spectra_l = np.mean(counts_l[logic_l, :], axis=0)

    logic_d   = (np.abs(ssfr_d.int_time[:, index_si]-int_time['si'])<0.00001) & (ssfr_l.shutter==1)
    spectra_d = np.mean(counts_d[logic_d, :], axis=0)

    spectra   = spectra_l - spectra_d
    spectra[spectra<=0.0] = np.nan
    rad_resp_si = spectra / int_time['si'] / resp['si']
    #\----------------------------------------------------------------------------/#


    # InGaAs
    #/----------------------------------------------------------------------------\#
    counts_l  = ssfr_l.spectra[:, :, index_in]
    counts_d  = ssfr_d.spectra[:, :, index_in]

    logic_l   = (np.abs(ssfr_l.int_time[:, index_in]-int_time['in'])<0.00001) & (ssfr_l.shutter==0)
    spectra_l = np.mean(counts_l[logic_l, :], axis=0)

    logic_d   = (np.abs(ssfr_d.int_time[:, index_in]-int_time['in'])<0.00001) & (ssfr_l.shutter==1)
    spectra_d = np.mean(counts_d[logic_d, :], axis=0)

    spectra   = spectra_l - spectra_d
    spectra[spectra<=0.0] = np.nan
    rad_resp_in = spectra / int_time['in'] / resp['in']
    #\----------------------------------------------------------------------------/#

    rad_resp = {'si':rad_resp_si,
                'in':rad_resp_in}

    return rad_resp



def cdata_rad_resp(
        fnames_pri=None,
        fnames_tra=None,
        fnames_sec=None,
        filename_tag=None,
        which_lamp='f-1324',
        which_lc='zen',
        which_ssfr='lasp|ssfr-a',
        wvl_joint=950.0,
        wvl_range=[350.0, 2200.0],
        ):

    # check SSFR spectrometer
    #/----------------------------------------------------------------------------\#
    which_ssfr = which_ssfr.lower()
    which_lab  = which_ssfr.split('|')[0]
    if which_lab == 'nasa':
        import ssfr.nasa_ssfr as ssfr_toolbox
    elif which_lab == 'lasp':
        import ssfr.lasp_ssfr as ssfr_toolbox
    else:
        msg = '\nError [cdata_rad_resp]: <which_ssfr=> does not support <\'%s\'> (only supports <\'nasa|ssfr-6\'> or <\'lasp|ssfr-a\'> or <\'lasp|ssfr-b\'>).' % which_ssfr
        raise ValueError(msg)
    #\----------------------------------------------------------------------------/#


    # check light collector
    #/----------------------------------------------------------------------------\#
    which_lc = which_lc.lower()
    #\----------------------------------------------------------------------------/#

    if fnames_pri is not None:
        pri_resp = cal_rad_resp(
                fnames_pri,
                resp=None,
                which_ssfr=which_ssfr,
                which_lc=which_lc,
                which_lamp=which_lamp,
                )
    else:
        msg = '\nError [cdata_rad_resp]: Cannot proceed without primary calibration files.'
        raise OSError(msg)

    if fnames_tra is not None:
        transfer = cal_rad_resp(
                fnames_tra,
                resp=pri_resp,
                which_ssfr=which_ssfr,
                which_lc=which_lc,
                which_lamp=which_lamp,
                )
    else:
        msg = '\nError [cdata_rad_resp]: Cannot proceed without transfer calibration files.'
        raise OSError(msg)

    if fnames_sec is not None:
        sec_resp = cal_rad_resp(
                fnames_sec,
                resp=transfer,
                which_ssfr=which_ssfr,
                which_lc=which_lc,
                which_lamp=which_lamp,
                )
    else:
        msg = '\nWarning [cdata_rad_resp]: Secondary/field calibration files are not available, use transfer calibration files for secondary/field calibration ...'
        warnings.warn(msg)
        sec_resp = cal_rad_resp(
                fnames_tra,
                resp=transfer,
                which_ssfr=which_ssfr,
                which_lc=which_lc,
                which_lamp=which_lamp,
                )

    wvls = ssfr_toolbox.get_ssfr_wavelength()

    wvl_start = wvl_range[0]
    wvl_end   = wvl_range[-1]
    logic_si = (wvls['%s_si' % which_lc] >= wvl_start) & (wvls['%s_si' % which_lc] <= wvl_joint)
    logic_in = (wvls['%s_in' % which_lc] >  wvl_joint)  & (wvls['%s_in' % which_lc] <= wvl_end)

    wvl_data      = np.concatenate((wvls['%s_si' % which_lc][logic_si], wvls['%s_in' % which_lc][logic_in]))
    pri_resp_data = np.hstack((pri_resp['si'][logic_si], pri_resp['in'][logic_in]))
    transfer_data = np.hstack((transfer['si'][logic_si], transfer['in'][logic_in]))
    sec_resp_data = np.hstack((sec_resp['si'][logic_si], sec_resp['in'][logic_in]))

    indices_sort = np.argsort(wvl_data)
    wvl      = wvl_data[indices_sort]
    pri_resp = pri_resp_data[indices_sort]
    transfer = transfer_data[indices_sort]
    sec_resp = sec_resp_data[indices_sort]

    if filename_tag is not None:
        fname_out = '%s_rad-resp_s%3.3di%3.3d.h5' % (filename_tag, int_time['si'], int_time['in'])
    else:
        fname_out = 'rad-resp_s%3.3di%3.3d.h5' % (int_time['si'], int_time['in'])

    f = h5py.File(fname_out, 'w')
    f['wvl']       = wvl
    f['pri_resp']  = pri_resp
    f['transfer']  = transfer
    f['sec_resp']  = sec_resp
    f.close()

    return fname_out



if __name__ == '__main__':

    pass
