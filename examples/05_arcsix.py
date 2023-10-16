import os
import sys
import glob
import datetime
import h5py
from pyhdf.SD import SD, SDC
from netCDF4 import Dataset
import numpy as np
from scipy import interpolate
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


_mission_   = 'arcsix'
_fdir_data_ = '/argus/pre-mission/%s' % _mission_
_fdir_hsk_  = '%s/raw/hsk'
_fdir_ssfr_ = '%s/raw/ssfr-b' % _fdir_data_
_fdir_spns_ = '%s/raw/spns-b' % _fdir_data_
_fdir_v0_   = '%s/processed'  % _fdir_data_
_fdir_v1_   = '%s/processed'  % _fdir_data_
_fdir_v2_   = '%s/processed'  % _fdir_data_


def cdata_arcsix_hsk_v0_placeholder(
        date,
        tmhr_range=[0.0, 24.0],
        fdir_data=_fdir_hsk_,
        fdir_out=_fdir_v0_,
        ):

    """
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    !! placeholder for in-field operation !!
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    process raw aircraft nav data
    """

    # read aircraft nav data (housekeeping file)
    #/----------------------------------------------------------------------------\#
    # fname = sorted(glob.glob('%s/*' % (fdir_data, date.strftime('%m_%d'))))[0]
    # data_hsk = ssfr.util.read_cabin(fname, tmhr_range=tmhr_range, time_units='sec')
    #\----------------------------------------------------------------------------/#

    # solar geometries
    #/----------------------------------------------------------------------------\#
    # jday0 = ssfr.util.dtime_to_jday(date)
    # jday = jday0 + data_hsk['tmhr']['data']/24.0
    # sza, saa = ssfr.util.cal_solar_angles(jday, data_hsk['long']['data'], data_hsk['lat']['data'], data_hsk['palt']['data'])
    #\----------------------------------------------------------------------------/#

    # save processed data
    #/----------------------------------------------------------------------------\#
    # fname_h5 = '%s/%s_HSK_%s_v0.h5' % (fdir_out_, _mission_.upper(), date.strftime('%Y-%m-%d'))

    # f = h5py.File(fname_h5, 'w')
    # f['tmhr'] = data_hsk['tmhr']['data']
    # f['lon']  = data_hsk['long']['data']
    # f['lat']  = data_hsk['lat']['data']
    # f['alt']  = data_hsk['palt']['data']
    # f['pit']  = data_hsk['pitch']['data']
    # f['rol']  = data_hsk['roll']['data']
    # f['hed']  = data_hsk['heading']['data']
    # f['jday'] = jday
    # f['sza']  = sza
    # f['saa']  = saa
    # f.close()
    #\----------------------------------------------------------------------------/#

    return

def cdata_arcsix_hsk_v0(
        date,
        tmhr_range=[0.0, 24.0],
        fdir_data=_fdir_hsk_,
        fdir_out=_fdir_v0_,
        ):

    """
    Usually this function is for processing aricraft housekeeping file in the field (also known as cabin file).

    Now for skywatch testing, we will use a fixed longitude and latitude
    """

    # create data_hsk for skywatch
    #/----------------------------------------------------------------------------\#
    tmhr = np.arange(86400.0)/3600.0
    lon0 = -105.24227862207863 # skywatch longitude
    lat0 =  40.01097849056196  # skywatch latitude
    alt0 =  4.0                # skywatch altitude
    pit0 = 0.0
    rol0 = 0.0
    hed0 = 0.0
    data_hsk = {
            'tmhr': {'data': tmhr, 'units': 'hour'},
            'long': {'data': np.repeat(lon0, tmhr.size), 'units': 'degree'},
            'lat' : {'data': np.repeat(lat0, tmhr.size), 'units': 'degree'},
            'palt': {'data': np.repeat(alt0, tmhr.size), 'units': 'meter'},
            'pitch'   : {'data': np.repeat(pit0, tmhr.size), 'units': 'degree'},
            'roll'    : {'data': np.repeat(rol0, tmhr.size), 'units': 'degree'},
            'heading' : {'data': np.repeat(hed0, tmhr.size), 'units': 'degree'},
            }
    #\----------------------------------------------------------------------------/#


    # solar geometries
    #/----------------------------------------------------------------------------\#
    jday0 = ssfr.util.dtime_to_jday(date)
    jday = jday0 + data_hsk['tmhr']['data']/24.0
    sza, saa = ssfr.util.cal_solar_angles(jday, data_hsk['long']['data'], data_hsk['lat']['data'], data_hsk['palt']['data'])
    #\----------------------------------------------------------------------------/#

    # save processed data
    #/----------------------------------------------------------------------------\#
    fname_h5 = '%s/%s_HSK_%s_v0.h5' % (fdir_out_, _mission_.upper(), date.strftime('%Y-%m-%d'))

    f = h5py.File(fname_h5, 'w')
    f['tmhr'] = data_hsk['tmhr']['data']
    f['lon']  = data_hsk['long']['data']
    f['lat']  = data_hsk['lat']['data']
    f['alt']  = data_hsk['palt']['data']
    f['pit']  = data_hsk['pitch']['data']
    f['rol']  = data_hsk['roll']['data']
    f['hed']  = data_hsk['heading']['data']
    f['jday'] = jday
    f['sza']  = sza
    f['saa']  = saa
    f.close()
    #\----------------------------------------------------------------------------/#

def cdata_arcsix_spns_v0(
        date,
        fdir_data=_fdir_data_,
        fdir_out=_fdir_v0_,
        ):

    """
    process raw SPN-S data
    """

    # read spn-s raw data
    #/----------------------------------------------------------------------------\#
    fdir = '%s/magpie/2023/dhc6/spn-s/raw/%s' % (fdir_data, date.strftime('%Y-%m-%d'))

    fname_dif = sorted(glob.glob('%s/Diffuse.txt' % fdir))[0]
    data0_dif = ssfr.lasp_spn.read_spns(fname=fname_dif)

    fname_tot = sorted(glob.glob('%s/Total.txt' % fdir))[0]
    data0_tot = ssfr.lasp_spn.read_spns(fname=fname_tot)
    #/----------------------------------------------------------------------------\#

    # read wavelengths and calculate toa downwelling solar flux
    #/----------------------------------------------------------------------------\#
    flux_toa = ssfr.util.get_solar_kurudz()

    wvl_tot = data0_tot.data['wavelength']
    f_dn_sol_tot = np.zeros_like(wvl_tot)
    for i, wvl0 in enumerate(wvl_tot):
        f_dn_sol_tot[i] = ssfr.util.cal_solar_flux_toa(wvl0, flux_toa[:, 0], flux_toa[:, 1])
    #\----------------------------------------------------------------------------/#

    # save processed data
    #/----------------------------------------------------------------------------\#
    fname_h5 = '%s/MAGPIE_SPN-S_%s_v0.h5' % (fdir_out, date.strftime('%Y-%m-%d'))

    f = h5py.File(fname_h5, 'w')

    g1 = f.create_group('dif')
    g1['tmhr']  = data0_dif.data['tmhr']
    g1['wvl']   = data0_dif.data['wavelength']
    g1['flux']  = data0_dif.data['flux']

    g2 = f.create_group('tot')
    g2['tmhr']  = data0_tot.data['tmhr']
    g2['wvl']   = data0_tot.data['wavelength']
    g2['flux']  = data0_tot.data['flux']
    g2['toa0']  = f_dn_sol_tot

    f.close()
    #\----------------------------------------------------------------------------/#

def cdata_arcsix_spns_v1(
        date,
        time_offset=0.0,
        fdir_data=_fdir_v0_,
        fdir_out=_fdir_v1_,
        ):

    """
    check for time offset and merge SPN-S data with aircraft data
    """

    # read hsk v0
    #/----------------------------------------------------------------------------\#
    fname_h5 = '%s/MAGPIE_HSK_%s_v0.h5' % (fdir_data, date.strftime('%Y-%m-%d'))
    f = h5py.File(fname_h5, 'r')
    jday = f['jday'][...]
    sza  = f['sza'][...]
    saa  = f['saa'][...]
    tmhr = f['tmhr'][...]
    lon  = f['lon'][...]
    lat  = f['lat'][...]
    alt  = f['alt'][...]
    pit  = f['pit'][...]
    rol  = f['rol'][...]
    hed  = f['hed'][...]
    f.close()
    #\----------------------------------------------------------------------------/#


    # read spn-s v0
    #/----------------------------------------------------------------------------\#
    fname_h5 = '%s/MAGPIE_SPN-S_%s_v0.h5' % (fdir_data, date.strftime('%Y-%m-%d'))
    f = h5py.File(fname_h5, 'r')
    f_dn_dif  = f['dif/flux'][...]
    wvl_dif   = f['dif/wvl'][...]
    tmhr_dif  = f['dif/tmhr'][...]

    f_dn_tot  = f['tot/flux'][...]
    wvl_tot   = f['tot/wvl'][...]
    tmhr_tot  = f['tot/tmhr'][...]
    f_dn_tot_toa0 = f['tot/toa0'][...]
    f.close()
    #/----------------------------------------------------------------------------\#


    # interpolate spn-s data to hsk time frame
    #/----------------------------------------------------------------------------\#
    flux_dif = np.zeros((tmhr.size, wvl_dif.size), dtype=np.float64)
    for i in range(wvl_dif.size):
        flux_dif[:, i] = ssfr.util.interp(tmhr, tmhr_dif, f_dn_dif[:, i])

    flux_tot = np.zeros((tmhr.size, wvl_tot.size), dtype=np.float64)
    for i in range(wvl_tot.size):
        flux_tot[:, i] = ssfr.util.interp(tmhr, tmhr_tot, f_dn_tot[:, i])
    #\----------------------------------------------------------------------------/#


    # save processed data
    #/----------------------------------------------------------------------------\#
    fname_h5 = '%s/MAGPIE_SPN-S_%s_v1.h5' % (fdir_out, date.strftime('%Y-%m-%d'))

    f = h5py.File(fname_h5, 'w')

    f['jday'] = jday
    f['tmhr'] = tmhr
    f['lon']  = lon
    f['lat']  = lat
    f['alt']  = alt
    f['sza']  = sza
    f['saa']  = saa
    f['pit']  = pit
    f['rol']  = rol
    f['hed']  = hed

    g1 = f.create_group('dif')
    g1['wvl']   = wvl_dif
    g1['flux']  = flux_dif

    g2 = f.create_group('tot')
    g2['wvl']   = wvl_tot
    g2['flux']  = flux_tot
    g2['toa0']  = f_dn_tot_toa0

    f.close()
    #\----------------------------------------------------------------------------/#

def cdata_arcsix_spns_v2(
        date,
        time_offset=0.0,
        fdir_data=_fdir_v1_,
        fdir_out=_fdir_v2_,
        ):

    """
    apply attitude correction to account for pitch and roll
    """

    # read spn-s v1
    #/----------------------------------------------------------------------------\#
    fname_h5 = '%s/MAGPIE_SPN-S_%s_v1.h5' % (fdir_data, date.strftime('%Y-%m-%d'))
    f = h5py.File(fname_h5, 'r')
    f_dn_dif  = f['dif/flux'][...]
    wvl_dif   = f['dif/wvl'][...]

    f_dn_tot  = f['tot/flux'][...]
    wvl_tot   = f['tot/wvl'][...]
    f_dn_toa0 = f['tot/toa0'][...]

    jday = f['jday'][...]
    tmhr = f['tmhr'][...]
    lon = f['lon'][...]
    lat = f['lat'][...]
    alt = f['alt'][...]
    sza  = f['sza'][...]
    saa  = f['saa'][...]

    pit = f['pit'][...]
    rol = f['rol'][...]
    hed = f['hed'][...]

    f.close()
    #/----------------------------------------------------------------------------\#


    # correction factor
    #/----------------------------------------------------------------------------\#
    mu = np.cos(np.deg2rad(sza))

    iza, iaa = ssfr.util.prh2za(pit, rol, hed)
    dc = ssfr.util.muslope(sza, saa, iza, iaa)

    factors = mu / dc
    #\----------------------------------------------------------------------------/#


    # attitude correction
    #/----------------------------------------------------------------------------\#
    f_dn_dir = f_dn_tot - f_dn_dif
    f_dn_dir_corr = np.zeros_like(f_dn_dir)
    f_dn_tot_corr = np.zeros_like(f_dn_tot)
    for iwvl in range(wvl_tot.size):
        f_dn_dir_corr[..., iwvl] = f_dn_dir[..., iwvl]*factors
        f_dn_tot_corr[..., iwvl] = f_dn_dir_corr[..., iwvl] + f_dn_dif[..., iwvl]
    #\----------------------------------------------------------------------------/#


    # save processed data
    #/----------------------------------------------------------------------------\#
    fname_h5 = '%s/MAGPIE_SPN-S_%s_v2.h5' % (fdir_out, date.strftime('%Y-%m-%d'))

    f = h5py.File(fname_h5, 'w')

    f['jday'] = jday
    f['tmhr'] = tmhr
    f['lon']  = lon
    f['lat']  = lat
    f['alt']  = alt
    f['sza']  = sza
    f['dc']   = dc

    g1 = f.create_group('dif')
    g1['wvl']   = wvl_dif
    g1['flux']  = f_dn_dif

    g2 = f.create_group('tot')
    g2['wvl']   = wvl_tot
    g2['flux']  = f_dn_tot_corr
    g2['toa0']  = f_dn_toa0

    f.close()
    #\----------------------------------------------------------------------------/#


    if False:
        wvl0 = 532.0
        index_wvl = np.argmin(np.abs(wvl_tot-wvl0))

        plt.close('all')
        fig = plt.figure(figsize=(18, 6))
        # plot
        #/--------------------------------------------------------------\#
        ax1 = fig.add_subplot(111)
        ax1.scatter(tmhr, mu*f_dn_toa0[index_wvl], s=1, c='k', lw=0.0)
        ax1.scatter(tmhr, f_dn_tot[..., index_wvl], s=1, c='r', lw=0.0)
        ax1.scatter(tmhr, f_dn_tot_corr[..., index_wvl], s=1, c='g', lw=0.0)
        ax1.set_title('MAGPIE %s (%d nm)' % (date.strftime('%Y-%m-%d'), wvl0))
        #\--------------------------------------------------------------/#

        patches_legend = [
                          mpatches.Patch(color='black' , label='TOA (Kurudz)'), \
                          mpatches.Patch(color='red'   , label='Original (Direct)'), \
                          mpatches.Patch(color='green' , label='Attitude Corrected (Direct)'), \
                         ]
        ax1.legend(handles=patches_legend, loc='upper right', fontsize=16)

        ax1.set_ylim((0.0, 2.2))
        ax1.set_xlabel('UTC Time [Hour]')
        ax1.set_ylabel('Irradiance [$\mathrm{W m^{-2} nm^{-1}}$]')

        # save figure
        #/--------------------------------------------------------------\#
        fig.subplots_adjust(hspace=0.3, wspace=0.3)
        _metadata = {'Computer': os.uname()[1], 'Script': os.path.abspath(__file__), 'Function':sys._getframe().f_code.co_name, 'Date':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        fig.savefig('%s_%s.png' % (_metadata['Function'], date.strftime('%Y-%m-%d')), bbox_inches='tight', metadata=_metadata)
        #\--------------------------------------------------------------/#
        plt.show()
        sys.exit()




def test(date):

    cdata_arcsix_hsk_v0(date)

    pass


if __name__ == '__main__':

    date = datetime.datetime(2023, 10, 13)

    test(date)
