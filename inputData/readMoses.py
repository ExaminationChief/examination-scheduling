#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
PATHS = os.getcwd().split('/')
PROJECT_PATH = ''
for p in PATHS:
    PROJECT_PATH += '%s/' % p
    if p == 'examination-scheduling':
        break
sys.path.append(PROJECT_PATH)

from collections import defaultdict
import re
import numpy as np
import pickle


def read_times_and_rooms(data = None):

    # read h vector
    colnames = list()

    start_times = defaultdict(float)
    end_times = defaultdict(float)
    mid_times = defaultdict(float)

    with open("%sinputData/Data/prfg_times.csv"%PROJECT_PATH) as ergebnis:
        for line in ergebnis:
            line = re.sub('\"', '', line)
            line = re.sub('\n', '', line)
            line = re.split(',', line)
            
            line.pop(0)
            prfgnbr = line[0]
            if re.match('.*PRFG.NUMMER.*', prfgnbr):
                colnames = line
            else:
                start_times[prfgnbr] = float(line[1])
                end_times[prfgnbr] = float(line[2])
                mid_times[prfgnbr] = float(line[3])
                
    duration = abs(np.array(start_times.values()) - np.array(end_times.values()) )

    # use start times as h
    slots_start = sorted(set(start_times.values()))
    slots_end = sorted(set(end_times.values()))
        
    h = slots_start
    
    # read room capacities
    colnames = list()
    room_capacity = defaultdict(int)
    campus_id = defaultdict(str)
    # Name;Name_lang;Sitzplaetze;Klausurplaetze_eng;ID_Raum;ID_Gebaeude;Gebaeude;ID_Raumgruppe;ID_Campus;Campus
    
    with open("%sinputData/Data/Raumuebersicht.csv"%PROJECT_PATH) as uebersicht:
        for line in uebersicht:
            line = re.sub('\"', '', line)
            line = re.sub('\n', '', line)
            line = re.split(';', line)
            
            line.pop(0)
            room_id = line[3]
            
            if re.match('.*ID_Raum.*', room_id):
                colnames = line
            else:
                room_capacity[room_id] = int(line[2])
                campus_id[room_id] = line[7]
            
    
    # read room conflicts
    colnames = list()
    start_times = defaultdict(float)
    end_times = defaultdict(float)
    
    with open("%sinputData/Data/raum_sperren.csv"%PROJECT_PATH) as ergebnis:
        for line in ergebnis:
            line = re.sub('\"', '', line)
            line = re.sub('\n', '', line)
            line = re.split(',', line)
            
            line.pop(0)
            room_id = line[0]
            if re.match('.*ID_RAUM.*', room_id):
                colnames = line
            else:
                start_times[room_id] = float(line[1])
                end_times[room_id] = float(line[2])
    
    locking_times_unordered = defaultdict(list)
    
    for room in start_times:
        for i in range(len(slots_start)-1):
            # determine position of locking start
            if start_times[room] >= slots_start[i] and start_times[room] <= slots_start[i+1]:
                #print "found a locked room!"
                j = i
                # search for position of locking end
                while( j < len(slots_start) - 1 ):
                    if end_times[room] < slots_start[j]:
                        break;
                    # on the way insert locking times to dict
                    locking_times_unordered[room].append(j)
                    j += 1
    
    #print locking_times_unordered
    locking_times = defaultdict(list)
    c = []
    for k, room in enumerate(room_capacity):        
        locking_times[k] = locking_times_unordered[room]
        c.append(room_capacity[room])
    
    print "Loading times and rooms: Correctness was not tested, but seems to work!"
    return h, locking_times, c
    
read_times_and_rooms()
