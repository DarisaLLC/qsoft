import datetime
import pyfits
from RedshiftMachine import LoadGCN

def t_mid(filepath=None, GRBid=None, delta=None, trigger=None, forcenongrb=False, time_dict=None):
    '''
    Given a fits file and the GRBid or trigger of a GRB, 
    this program returns the t-mid for PAIRITEL as a float in seconds. 
    
    If delta = True, t_mid will find the difference of StartCPU 
    and StopCPU in seconds
    
    time_dict will override the need for filepath
    {'utburst':'2012-01-19 04:04:30.21',
     'STOP_CPU':'2013-01-19 08:07:24.094335',
     'STRT_CPU':'2013-01-19 08:05:05.498592'}
     
     if 'utburst' is not in the time dict, then it will not be a known_grb
    
    '''
    if filepath != None and time_dict != None:
        raise ValueError('Please specify either filepath OR time_dict, not both')
    if filepath == None and time_dict == None:
        raise ValueError('Must specify either filepath OR time_dict')
    if filepath != None:
        header = pyfits.open(filepath)
        starttime = header[0].header['STRT_CPU']
        stoptime = header[0].header['STOP_CPU']
    elif time_dict != None:
        starttime = time_dict['STRT_CPU']
        stoptime = time_dict['STOP_CPU']
        
    start = datetime.datetime.strptime(starttime.split('.')[0], "%Y-%m-%d %H:%M:%S")
    stop = datetime.datetime.strptime(stoptime.split('.')[0], "%Y-%m-%d %H:%M:%S")
    
    #handle the fractions of a second:
    start_microseconds_str = starttime.split('.')[1] 
    stop_microseconds_str = stoptime.split('.')[1]
    if len(start_microseconds_str) != 6:
        raise ValueError("The length of the microseconds split in STRT_CPU is not 6; Check header file")
    else:
        start_microseconds = int(start_microseconds_str)
    if len(start_microseconds_str) != 6:
        raise ValueError("The length of the microseconds split in STRT_CPU is not 6; Check header file")
    else:
        stop_microseconds = int(stop_microseconds_str)
    
    start = start + datetime.timedelta(microseconds=start_microseconds)
    stop = stop + datetime.timedelta(microseconds=stop_microseconds)
    
    
    if not delta:

        durdiv2 = (stop - start)/2 + start
        #print "durdiv2 is " +  str(durdiv2)
        print 'start time is ' + str(start)
        print 'stop time is ' + str(stop)
        
        known_grb = False
        
        if filepath != None:
            trg = None
        
            # if triggerid given, attempt to grab burst time from GCN notices
            if not GRBid:
                if not trigger:
                    print 'Trigger ID not specified; attempting to parse from file header'
                    targetname = header[0].header['TRGTNAME']
                    if targetname[0:5] == 'swift':
                        try:
                            trg = int(targetname[6:])
                            print "GRB Trigger ID determined to be %i" % trg
                            known_grb = True                        
                        except:
                            print 'Cannot Parse target id from swift target name %s' % targetname
                else:
                    trg = trigger
            
                if trg:
                    gcndict = LoadGCN.LoadGCN(trg)
                    known_grb = gcndict.successful_load                    
            else:
                gcndict = LoadGCN.LoadGCN(GRBid)
                known_grb = gcndict.successful_load
        elif time_dict != None:
            if 'utburst' in time_dict:
                known_grb = True        
            else:
                known_grb = False
        
        if forcenongrb:
            known_grb=False
        print "It is %s that this event is a known GRB." % str(known_grb)
        
        
        if known_grb:
            if filepath != None:
                GRBtime = gcndict.pdict['grb_time_str']
                GRBdate = gcndict.pdict['grb_date_str']
                
                GRBcomb = GRBdate + ' ' + GRBtime
            elif time_dict != None:
                GRBcomb = time_dict['utburst']
            try:
                GRB = datetime.datetime.strptime(GRBcomb.split('.')[0], "%y/%m/%d %H:%M:%S")
            except:
                try:
                    GRB = datetime.datetime.strptime(GRBcomb.split('.')[0], "%Y-%m-%d %H:%M:%S")
                except:
                    raise Exception("Can't parse utburst..")
                    
            t_mid = durdiv2 - GRB  
            print durdiv2
            
            t_mid_str = str(t_mid)

            #print t_mid_str

            if 'days' in t_mid_str:
                t_mid_days = float(t_mid_str.split(' days')[0]) * (24.)
            elif 'day' in t_mid_str:
                t_mid_days = float(t_mid_str.split(' day')[0]) * (24.)
            else:
                t_mid_days = 0.


            #edited for photloop-------
            t_mid_str_2 = t_mid_str.split()[-1]
            t_mid_time_list = t_mid_str_2.split(':')

            #print t_mid_time_list
            t_mid_time_hour = float(t_mid_time_list[0]) + float(t_mid_time_list[1])*(1/60.) + float(t_mid_time_list[2])*(1/3600.)
            t_mid_hour = t_mid_days + t_mid_time_hour
            t_mid_sec = t_mid_hour*3600.


            #original-------

            #t_mid_time_list = t_mid_str[::-1][0:8][::-1].split(':')

            #print t_mid_time_list
            #t_mid_time_hour = float(t_mid_time_list[0]) + float(t_mid_time_list[1])*(1/60.) + float(t_mid_time_list[2])*(1/3600.)
            #t_mid_hour = t_mid_days + t_mid_time_hour



        else:
            # tmid is just the mjd middle point between start and stop exposure times
            mjd_start = datetime.datetime(1858, 11, 17)
            mjd = durdiv2 - mjd_start
            t_mid_sec = mjd.days*86400 + mjd.seconds + mjd.microseconds/1e6
        
        print 't_mid in seconds is ' + str(t_mid_sec)
        return float(t_mid_sec)
                        


    else:
        
        duration = stop - start
        durstr = str(duration)

        if 'days' in durstr:
            durdays = float(t_mid_str.split(' days')[0]) * (24.)
        else:
            durdays = 0.

        dur_list = durstr.split(':')

        #print dur_list
        dur_time_hour = float(dur_list[0]) + float(dur_list[1])*(1/60.) + float(dur_list[2])*(1/3600.)
        dur_hour = durdays + dur_time_hour
        dur_sec = dur_hour*3600.

        print 'duration in seconds is ' + str(dur_sec)
        if delta:
            return dur_sec
        