import matplotlib
import os
import numpy as np
from numpy import array as arr
import cosmocalc
from Phot import t_mid
from MiscBin import qPickle
import pidly
import glob
import pyfits

# autophot, '051008_g.fits', '051008.sdss', 'allhosts.pos', rad=1.2

if not os.environ.has_key("Q_DIR"):
    print "You need to set the environment variable Q_DIR to point to the"
    print "directory where you have Q_DIR installed"
    sys.exit(1)
storepath = os.environ.get("Q_DIR") + '/store/'
loadpath = os.environ.get("Q_DIR") + '/load/'
sextractor_bin = "sex"

idl_path = '/Applications/itt/idl71/bin/idl'
idl = pidly.IDL(idl_path)

class Event():
    """docstring for Event"""
    def __init__(self, eventname):
        self.eventname = eventname
        
class Image():
    """docstring for Image"""
    def __init__(self, imagefilename,objectfile,calfile=None,objectname="UnknownSource",ap=1.2,telescope=None,forcefilter=None):
        self.imagefilename = imagefilename
        self.objectname = objectname # could potentially look in header for this name
        if not calfile:
            print "No calibration file specified; attempting to grab SDSS Calibration"
            calpath = storepath + objectname + 'sdss.txt'
            self.get_sdss_calibration(calpath) 
            if self.sdssfield:
                self.calfile = self.sdsscal
                print "SDSS Calibration file created"
            else:
                self.calfile=None
                print "Warning: No SDSS calibration; Please provide your own calibration field and run again."
        else:
            self.calfile = calfile
        self.objectfile = objectfile
        self.telescope = telescope
        self.ap = ap
        self.telescope = telescope
        self.forcefilter = forcefilter
        
    def do_phot(self):
        '''
        q_phot.do_phot subkeys:
        ['calib_stars',
         'faintest_s2n',
         'HJD_mid',
         'STOP_CPU',x
         'targ_s2n',
         'sex_faintest',
         'N_dither',
         'HJD_start',
         '2mass_abs_avg_dev',
         'STRT_CPU',x
         't_mid',
         'FileName',x
         'filter',x
         'targ_mag',x
         'Aperture',x
         'HJD_stop',
         'targ_flux',
         'zp',x
         'EXPTIME']x
        '''

        image_name = self.imagefilename

        photdict = {'FileName':image_name}

        # open up the file and read the header
        hdulist = pyfits.open(image_name)
        image_data = hdulist[0].data
        imagefile_header = hdulist[0].header
        hdulist.close()

        # determine the telescope, if possible
        if imagefile_header.has_key("TELESCOP"):
            TELESCOP = str(imagefile_header["TELESCOP"])
            if TELESCOP.strip() == 'K.A.I.T.':
                scope = 'kait'
            elif TELESCOP.find('PAIRITEL') != -1:
                scope = 'pairitel'
            else:
                scope = 'unknown'
        else:
            scope = 'unknown'


        # error checking of individual telescopes
        if scope == 'kait':
            #if KAIT, verify that ccdproc has been done
            if not imagefile_header.has_key('BIASID'):
                raise Exception("BIASID doesnt exist for KAIT image")
            if not imagefile_header.has_key('DARKID'):
                raise Exception("DARKID doesnt exist for KAIT image")
            if not imagefile_header.has_key('FLATID'):
                raise Exception("FLATID doesnt exist for KAIT image")


        if imagefile_header.has_key("STRT_CPU"): #PAIRITEL
            strt_cpu = str(imagefile_header["STRT_CPU"])
            stop_cpu = str(imagefile_header["STOP_CPU"])
        elif imagefile_header.has_key("DATE-OBS") and imagefile_header.has_key("UT"): #KAIT

            bbb = str(imagefile_header["DATE-OBS"])
            ccc = str(imagefile_header['UT'])
            strt_cpu = bbb[6:10]+'-'+bbb[3:5]+'-'+bbb[0:2] + ccc
            stop_cpu = 'no_stop_cpu' # could just add the exposure time..
        else:
            strt_cpu = 'no_strt_cpu'
            stop_cpu = 'no_stop_cpu'


        photdict.update({'STRT_CPU':strt_cpu})
        photdict.update({'STOP_CPU':stop_cpu})    
        photdict.update({'Aperture':self.ap})



        #Performing Photometry
        IDL_command = "autophot, '" + str(self.imagefilename) + "', '" + str(self.calfile) +  "', '"  + str(self.objectfile) + "', rad=" + str(self.ap)+", filter='"+str(self.forcefilter)+"'"
        idl(IDL_command)
        # 
        # #Read the filename
        filename = 'tmpphot.txt'
        f=open(filename,'r')
        lines = f.readlines()
        for line in lines:
            if line[0:4] == "Phot":
                # ['Phot:', '051008', ':', 'g', '=', '24.46', '+/-', '0.06', '(+/-', '0.01)']
                photlist = line.split()
                filtstr = photlist[3]
                mag = float(photlist[5])
                magerr = float(photlist[7])
                syserr = float(photlist[9].strip(')'))

                # to match qphot targ mag format of tuple of mag and mag err
                # here add the stat error and sys error in quadrature
                # not 100% correct since there is some covariance, but roughly right
                targ_mag = (mag, np.sqrt(magerr**2+syserr**2))
                photdict.update({'targ_mag':targ_mag})
                photdict.update({'filter':filtstr})

            elif line[0:4] == "Expt":
                explist = line.split()
                exptime = float(explist[1])
                photdict.update({'EXPTIME':exptime})

            elif line[0:18] == 'Measured zeropoint':
                zplist = line.split()
                zp = (float(zplist[-3]),float(zplist[-1]))
                photdict.update({'zp':zp})

        self.imagedict = photdict
        return photdict


    def get_sdss_calibration(self,sdsscal):
        #IDL> printsdss, 'OBS1_R.fits', outfile="calib.txt"

        #Performing Photometry
        IDL_command = "printsdss, '" + str(self.imagefilename) + "', outfile='" + str(sdsscal) +  "', unc=1"  
        idl(IDL_command)
        self.sdsscal = sdsscal
        if os.path.exists(self.sdsscal):
            self.sdssfield=True
        else:
            self.sdssfield=False
    
    
    def p_photreturn(self,clobber=False):
        '''
        attempt to build up same structure as the photdict from q_phot

        keys: filename


        '''
        photdict={}

        filepath = storepath + self.objectname + 'ap' + str(self.ap)  
        # if calregion:
        #     calibration_list = openCalRegion(calregion)
        #     n_calstars = len(calibration_list)
        #     filepath += '_WithCalReg' + str(n_calstars)
        # if stardict:
        #     filepath += '_WithDeepStack'
        filepath += '.data'
        while clobber == False:     # why did i make this a while loop?? lol
            if os.path.isfile(filepath) == True:
                data = qPickle.load(filepath)
                if self.imagefilename in data:
                    return data
                else:
                    clobber = True
            else:
                clobber = True


        while clobber == True:

            if os.path.isfile(filepath) == False:
                photdict = {}  
            else:
                #f = file(filepath)
                photdict = qPickle.load(filepath) # This line loads the pickle file, enabling photLoop to work                

            # create dictionary for file
            data = self.do_phot()
            #rerun to get upper limit??
            
            label = data['FileName']
            # somehow update time here?
            # time = float(t_mid.t_mid(filename, trigger = trigger_id))
            # terr = float(t_mid.t_mid(filename, delta = True, trigger = trigger_id))/2.
            # timetuple = (time, terr)
            # data.update({'t_mid':timetuple})
            photdict.update({label:data})
            qPickle.save(photdict, filepath, clobber = True)
            return photdict


        qPickle.save(photdict, filepath, clobber = True)


        return photdict


def kait_data_check(directory):
    globlist = glob.glob(directory)

    for filestr in globlist:
        if 'fit' in filestr.split('.')[-1]: #confirm that fits file. could be fit, fits, fts.. 
            hdulist = pyfits.open(filestr)
            header = hdulist[0].header
            hdulist.close()
            string = "%s \t %s \t %s \t %s \t %s" % (filestr, header['UT'], header['EXPTIME'], header['FILTERS'], header['AIRMASS'])
            print string
            