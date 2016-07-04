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

from model.data_format import force_data_format

def read_columns(datname, key, cols, sep=","):
    '''
    Read csv file and extract data with column names in cols. Takes first value found!
    '''
    columns = defaultdict(dict)
    colnames = []
    with open("%sinputData/%s"%(PROJECT_PATH, datname)) as csvfile:
        for line in csvfile:
            line = re.sub('\"', '', line)
            line = re.sub('\n', '', line)
            line = re.sub('\r', '', line)
            line = re.split(sep, line)


            assert len(line) > len(cols)
            
            #print colnames

            if len(colnames) == 0:
                colnames = line
            else:
                
                # get identifier
                if type(key) == list:
                    ident = " ".join([ line[colnames.index(k)] for k in key ])
                else:
                    ident = line[colnames.index(key)]
                
                for i in range(0, len(colnames)):
                    name = colnames[i]
                    if name in cols and ident not in columns[name]:
                        columns[name][ident] = line[i]
                    
    return columns


def read_result_times(semester):
    # read times from result file
    
    if semester == "15W":
        key = ["PRFG.NUMMER", "TERMIN"]
    else:
        key = "PRFG.NUMMER"
    # "","PRFG.NUMMER","startHours","endHours","startDate","endDate"
    prfg = read_columns("%s/prfg_times.csv" %semester, key, ["startHours", "endHours", "startDate", "endDate"], sep=",")

    startHours = prfg["startHours"]
    startDate = prfg["startDate"]
    
    exam_times = dict()
    for exam in startHours:
        exam_times[exam] = float(startHours[exam])
    
    return exam_times, startDate


def read_result_rooms(semester):
    # read rooms from result file
    
    # "","PRFG.NUMMER","startHours","endHours","startDate","endDate"
    
    cols = []
    for i in range(1, 10):
        cols.append("ORT_CODE_0%d" %i)
    for i in range(10, 31):
        cols.append("ORT_CODE_%d" %i)
        
    if semester == "15W":
        key = ["PRFG-NUMMER", "TERMIN"]
    else:
        key = "PRFG-NUMMER"
        
    prfg = read_columns("%s/Ergebnis_%s.csv" %(semester, semester), key, cols, sep=";")
    
    exam_rooms = defaultdict(set)
    for col in prfg:
        for exam in prfg[col]:
            exam_rooms[exam].add(prfg[col][exam])
    
    for exam in exam_rooms:
        exam_rooms[exam] = list(exam_rooms[exam])
        if '' in exam_rooms[exam]:
            exam_rooms[exam].remove('')
    
    exam_rooms = { exam: exam_rooms[exam] for exam in exam_rooms if len(exam_rooms[exam]) > 0 }
    
    return exam_rooms


def read_rooms():
    
    # Name;Name_lang;Sitzplaetze;Klausurplaetze_eng;ID_Raum;ID_Gebaeude;Gebaeude;ID_Raumgruppe;ID_Campus;Campus
    room_overview = read_columns("Data/Raumuebersicht.csv", "ID_Raum", ["Klausurplaetze_eng", "ID_Campus"], sep=";")
        
    return room_overview["Klausurplaetze_eng"], room_overview["ID_Campus"]
    
    
    
def read_locked_rooms(semester, rooms, h):
    print semester
    # "","ID_RAUM","startTime","endTime","startDate","endDate"
    if semester == "15W":
        key = "RAUM_CODE"
        full_key = ["RAUM_CODE", "startDate", "endDate"]
    else:
        key = "ID_RAUM"
        full_key = "ID_RAUM"
    
    room_data = read_columns("%s/raum_sperren.csv" %semester, full_key, [key, "startTime", "endTime", "startDate","endDate"], sep=",")
    
    room_ids = room_data[key]
    start_hours = room_data["startTime"]
    end_hours = room_data["endTime"]
    
    # save locking times in dictionary
    room_locking_times = defaultdict(list)
    
    # find time indices for which rooms are locked
    for key in start_hours:
        room = room_ids[key]
        if room not in rooms:
        #    print "ROOM NOT USED!"
            continue
        else:
            k = rooms.index(room)
        for i in range(len(h)-1):
            # determine position of locking start
            if float(start_hours[key]) > h[i] and float(start_hours[key]) <= h[i+1]:
                j = i+1
                
                # search for position of locking end
                while( j < len(h) ):
                    
                    if float(end_hours[key]) < h[j]:
                        break;
                    # on the way insert locking times to dict
                    if j not in room_locking_times[k]:
                        room_locking_times[k].append(j)
                    j += 1
    return room_locking_times


def read_teilnehmer(semester):
    #LV_NUMMER;LV_TITEL;LV_SEMESTER;DATUM;ANZ_TEILNEHMER
    
    filename = "Teilnehmer/Teilnehmer_15.csv"
    
    if semester == "15W":
        key = ["LV_NUMMER", "DATUM"]
    else:
        key = "LV_NUMMER"
        
    students = read_columns(filename, key, ["LV_SEMESTER", "ANZ_TEILNEHMER"], sep=";")
    
    
    exam_students = dict()
    for exam in students["ANZ_TEILNEHMER"]:
        
        if students["LV_SEMESTER"][exam] != semester:
            continue

        # IN0039;Praktikum: Game Engine Design;15S;24/07/2015;195
        # split key, we need to rearrange date
        match = re.search("\d{2}.\d{2}.\d{4}", exam)
        if match is None:
            #print "ERROR!", exam
            continue
        
        datum = match.group()
        lv_nr = re.sub("\s*%s" %datum, "", exam)
        
        datum = re.split("\/", datum)
        if len(datum) < 2:
            #print "ERROR!", exam
            continue
        
        datum = "%d/%d/%s" %(int(datum[1]), int(datum[0]), datum[2])
        
        key = "%s %s" %(lv_nr, datum)
        
        if key not in exam_students:
            exam_students[key] = int(students["ANZ_TEILNEHMER"][exam])
        else:
            exam_students[key] += int(students["ANZ_TEILNEHMER"][exam])
            
    return exam_students
    
    
def read_students(semester):
    #MODUL;T_NR;DATUM_T1;ANZ_STUD_MOD1;STUDIS_PRUEF1_GES;STUDIS_PRUEF1_ABGEMELDET;STUD_NICHT_ERSCHIENEN_PRUEF1;MODUL2;T_NR2;DATUM_T2;SEMESTER;ANZ_STUD_MOD2;STUDIS_PRUEF2_GES;STUDIS_PRUEF2_ABGEMELDET;STUD_NICHT_ERSCHIENEN_PRUEF2
    
    # Name;Name_lang;Sitzplaetze;Klausurplaetze_eng;ID_Raum;ID_Gebaeude;Gebaeude;ID_Raumgruppe;ID_Campus;Campus
    
    anmelde_data = semester
    if semester == "16S":
        anmelde_data = "15S"
    
    filename = "Conflicts/%s.csv" %anmelde_data
    
    if semester == "15W":
        key1 = ["MODUL", "DATUM_T1"]
        key2 = ["MODUL2", "DATUM_T2"]
    else:
        key1 = "MODUL"
        key2 = "MODUL2"
        
    students_abs_1 = read_columns(filename, key1, ["STUDIS_PRUEF1_GES", "STUDIS_PRUEF1_ABGEMELDET", "STUD_NICHT_ERSCHIENEN_PRUEF1"], sep=";")
    
    students_abs_2 = read_columns(filename, key2, ["STUDIS_PRUEF2_GES", "STUDIS_PRUEF2_ABGEMELDET", "STUD_NICHT_ERSCHIENEN_PRUEF2"], sep=";")
    
    exam_students = dict()
    for exam in students_abs_1["STUDIS_PRUEF1_GES"]:
        exam_students[exam] = int(students_abs_1["STUDIS_PRUEF1_GES"][exam])# - int(students_abs_1["STUDIS_PRUEF1_ABGEMELDET"][exam])
        if exam_students[exam] < 0:
            exam_students[exam] = int(students_abs_2["STUDIS_PRUEF2_GES"][exam])
        
    
    for exam in students_abs_2["STUDIS_PRUEF2_GES"]:
        exam_students[exam] = int(students_abs_2["STUDIS_PRUEF2_GES"][exam])# - int(students_abs_2["STUDIS_PRUEF2_ABGEMELDET"][exam])
        if exam_students[exam] < 0:
            exam_students[exam] = int(students_abs_2["STUDIS_PRUEF2_GES"][exam])
            
    return exam_students
    
    

def read_conflicts(semester, exams = None, threshold = 0):
    #MODUL;T_NR;DATUM_T1;ANZ_STUD_MOD1;STUDIS_PRUEF1_GES;STUDIS_PRUEF1_ABGEMELDET;STUD_NICHT_ERSCHIENEN_PRUEF1;MODUL2;T_NR2;DATUM_T2;SEMESTER;ANZ_STUD_MOD2;STUDIS_PRUEF2_GES;STUDIS_PRUEF2_ABGEMELDET;STUD_NICHT_ERSCHIENEN_PRUEF2
    
    anmelde_data = semester
    if semester == "16S":
        anmelde_data = "15S"
    filename = "Conflicts/%s.csv" %anmelde_data
    
    Q_abs = defaultdict(int)
    colnames = []
    
    with open("%sinputData/%s"%(PROJECT_PATH, filename)) as csvfile:
        for line in csvfile:
            line = re.sub('\"', '', line)
            line = re.sub('\n', '', line)
            line = re.split(';', line)
            
            if len(colnames) == 0:
                colnames = line
            else:
                
                ident1 = line[colnames.index("MODUL")]
                ident2 = line[colnames.index("MODUL2")]
                if semester == "15W":
                    ident1 = ident1 + " " + line[colnames.index("DATUM_T1")]
                    ident2 = ident2 + " " + line[colnames.index("DATUM_T2")]
                    
                #print exams
                # make sure the exam is used for our solution
                if exams is not None and ident1 not in exams:
                    continue
                if exams is not None and ident2 not in exams:
                    continue
                
                assert line[colnames.index("ANZ_STUD_MOD1")] == line[colnames.index("ANZ_STUD_MOD2")]
                
                # get conflicts
                n_conflicts = int(line[colnames.index("ANZ_STUD_MOD1")])
                
                # build Q matrix
                if n_conflicts > threshold:
                    Q_abs[ident1, ident2] = n_conflicts
                    
                
    print "read conflicts"
    n = len(exams)
    Q = [[0 for i in range(n)] for i in range(n)]
    K = defaultdict(int)
    conflicts = defaultdict(list)
    
    for i, e1 in enumerate(exams):
        for j, e2 in enumerate(exams):
            if Q_abs[e1, e2] > 0:
                Q[i][j] = 1
                Q[j][i] = 1
                if j not in conflicts[i]:
                    conflicts[i].append(j)
                if i not in conflicts[j]:
                    conflicts[j].append(i)
                
                K[i,j] = Q_abs[e1, e2]
                if (e2, e1) in Q_abs:
                    K[i,j] = max(K[i,j], Q_abs[e2, e1])
                K[j,i] = K[i,j]
              
    return Q, conflicts, K
    
    
def get_duplicate_exams(exams, exam_rooms, exam_times):
    
    '''
        Some exams are in the same room in the same time slot. This happens because we define the slots differently.
        The method returns those exams which are to be dropped!
    '''
    
    duplicates = defaultdict(set)
    for exam in exams:
        for exam2 in exams:
            if exam2 in duplicates[exam] or exam in duplicates[exam2]:
                continue
            if exam_times[exam] == exam_times[exam2]:
                if any( room in exam_rooms[exam2] for room in exam_rooms[exam] ):
                    #print exam, exam2, exam_rooms[exam], exam_rooms[exam2]
                    duplicates[exam].add(exam2)
    
    # throw out those duplicate exams with the least number of rooms
    drop_exams = set()
    for exam in duplicates:
        dupl = sorted(duplicates[exam])
        if len(dupl) > 1:
            n_rooms = [ len(exam_rooms[exam2]) for exam2 in dupl ]
            max_rooms = n_rooms.index(max(n_rooms))
            for j in range(len(n_rooms)):
                if j != max_rooms:
                    drop_exams.add(dupl[j])
    return drop_exams

    
def get_weeks(h):
    '''
        Returns an heuristic for when a week starts and when it ends.
        Data structure is a dictionary for week number and a list with [begin, end].
    '''
    
    distances = defaultdict(int)
    for i in range(1, len(h)):
        d = h[i] - h[i-1]
        distances[d] += 1
    #for w in distances:
        #print w, distances[w]
        
    D = [d for d in distances][2]
    
    counter = 0
    weeks = defaultdict(list)
    for i in range(1, len(h)):
        weeks[counter] += [h[i-1]]
        if h[i] - h[i-1] >= D:
            counter += 1
    
    return weeks


def get_faculty_weeks(exams, exam_times, week_slots, verbose = False):
    '''
        For each faculty get lists of weeks where exams are held
    '''
    
    # get faculties
    exam_faculty = {exam: re.search("\D+\d", exam).group()[0:-1] for exam in exams }
    faculties = sorted(set(exam_faculty.values()))
    if verbose: print faculties
    
    
    ## old: do it for each slot
    #faculty_periods = defaultdict(list)
    #for exam in exams:
        #for faculty in faculties:
            #if re.match(faculty, exam) is not None:
                #faculty_periods[faculty].append(exam_times[exam])
                #break
    
    # get examination periods for each faculty in weeks:
    faculty_periods = defaultdict(list)
    for exam in exams:
        faculty = exam_faculty[exam]
        for week in week_slots:
            if week not in faculty_periods[faculty] and exam_times[exam] in week_slots[week]:
                faculty_periods[faculty].append(week)
                break
    
    return faculty_periods


def get_possible_exam_slots(exams, exam_times, verbose=False):
    '''
        For each exam get the time slots which can be used to schedule this exam!
    '''
    
    # get time slots of weeks
    week_slots = get_weeks(sorted(set(exam_times.values())))
    #if verbose:
        #for w in week_slots:
            #print w, week_slots[w]
        
    
    # get examination periods for each faculty in weeks:
    faculty_weeks = get_faculty_weeks(exams, exam_times, week_slots, verbose = verbose)
    #if verbose:
        #for f in faculty_weeks:
            #print f, sorted(faculty_weeks[f])
    
    # get faculty of each exam
    exam_faculty = { exam: re.search("\D+\d", exam).group()[0:-1] for exam in exams }
    
    
    exam_slots = defaultdict(list)
    
    for exam in exams:
        faculty = exam_faculty[exam]

        # determine week of exam:
        w = 0
        while w < len(week_slots):
            if exam_times[exam] in week_slots[w]:
                break
            else: 
                w += 1
        
        exam_slots[exam] += week_slots[w]
        
        # for all connecting weeks to the left, add slots
        w2 = w-1
        while w2 > 0:
            if w2 in faculty_weeks[faculty]:
                exam_slots[exam] += week_slots[w2]
            else:
                break
            w2 -= 1
        
        # for all connecting weeks to the right, add slots
        w3 = w+1
        while w3 < len(week_slots):
            if w3 in faculty_weeks[faculty]:
                exam_slots[exam] += week_slots[w3]
            else:
                break
            w3 += 1
    
    
    #for exam in exam_faculty:
        #if "MA" in exam:
            #print exam, exam_times[exam]
            #print sorted(faculty_weeks[exam_faculty[exam]])
            #print sorted(exam_slots[exam])
    
    
    return exam_slots
 
 
def get_exam_rooms(exams, result_rooms, room_campus_id):
    '''
        For each exam get the rooms which are located at the campus the exam is to be held.
    '''
    all_rooms = set([room for exam in result_rooms for room in result_rooms[exam]])
            
    exam_rooms = defaultdict(list)
    for exam in exams:
        camps = set([ room_campus_id[room] for room in result_rooms[exam] ])
        for room in all_rooms:
            if room in room_campus_id and room_campus_id[room] in camps:
                exam_rooms[exam].append(room)
    
    return exam_rooms
    

@force_data_format
def read_data(semester = "16S", threshold = 0, pre_year_data = False, make_intersection=True, verbose=False, max_periods = None):
    '''
        @ Param make_intersection: Use exams which are in tumonline AND in szenarioergebnis
    '''
    
    #semester = "15W"
    assert semester in ["15W", "16S"], "Wir haben nur Ergebnisse für Winder 15 und Sommer 16!"
    
    print "Semester:", semester
    
    #print "Loading data: Data needs verification!"
    if max_periods is not None:
        print "WARNING: max_periods is not implemented any more!"
    
    # load times from szenarioergebnis
    result_times, result_dates = read_result_times(semester)
    
    # load room results from szenarioergebnis
    result_rooms = read_result_rooms(semester)
    
    # load room capacities
    room_capacity, room_campus_id = read_rooms()
    
    # load number of students registered for each exam
    if semester in ["15W", "16S"]:
        exam_students = read_teilnehmer(semester)
        # print sorted([exam for exam in result_times if exam not in exam_students])
        
        if pre_year_data:
            print "Pre year data is currently turned off!"
    else:
        exam_students = read_students(semester)
        
        # load number of students registered for each exam
        if pre_year_data:
            unknown_exams = 0
            presem = "14W" if semester == "15W" else "14S"
            
            pre_students = read_students(presem)
            
            for exam in exam_students:
                exam_renamed = re.sub("\s+\d+\/\d+\/\d+", "", exam)
                if exam_renamed in pre_students:
                    exam_students[exam] = pre_students[exam_renamed]
                else:
                    unknown_exams += 1
                    exam_students[exam] = 0
            if verbose: print "unknown predata", unknown_exams, len(exam_students)
        
            
    # get exams in the MOSES result
    exams = [exam for exam in result_times]
    if verbose: print "Number of exams", len(exams)
    
    exams = [exam for exam in exams if exam in exam_students and exam_students[exam] > 0]
    if verbose: print "Number of exams", len(exams)
    
    if verbose: print "Drop exams without students", len([exam for exam in exams if exam not in exam_students])
    if verbose: print "Drop exams without rooms", len([exam for exam in exams if exam not in result_rooms or len(result_rooms[exam]) == 0])
    
    # filter all exams for which we have student data
    exams = [exam for exam in result_times if exam in exam_students]
    if verbose: print "Number of exams", len(exams)
    
    for exam in exams: assert exam in exam_students
    
    #for exam in sorted(exams):
        #if "MA" in exam:
            #print exam, exam_students[exam]
    
    # filter all exams for which we know the room
    exams = [exam for exam in exams if exam in result_rooms and len(result_rooms[exam]) > 0]
    if verbose: print "Number of exams", len(exams)
    
    for exam in exams: assert exam in result_rooms
    
    # filter all exams for which we have room data
    exams = [exam for exam in exams if all(room in room_capacity for room in result_rooms[exam])]
    if verbose: print "Number of exams", len(exams)
    
    # detect duplicates, i.e. exams at the same time slot in the same room. Drop smaller ones
    drop_exams = get_duplicate_exams(exams, result_rooms, result_times)
    if verbose: print "Drop duplicates", len(drop_exams)
    
    exams = [ exam for exam in exams if exam not in drop_exams ]
    
    if verbose: print "Number of exams", len(exams)
    
    # build exam data structures
    if verbose: print "Number of timeslots", len(sorted(set(result_times.values())))
    
    #h = sorted(set([result_times[exam] for exam in exams]))
    h = sorted(set(result_times.values()))
    s = [exam_students[exam] for exam in exams]
    
    if verbose: print "Number of timeslots", len(h)
    
    # for each exam determine the possible time slots according to examination periods
    exam_slots = get_possible_exam_slots(exams, result_times, verbose=verbose)
    if verbose: print "Exam slots", len(exam_slots)
    
    # get index format for exam slots (for ILP)
    exam_slots_index = defaultdict(list)
    for exam in exam_slots:
        for slot in exam_slots[exam]:
            exam_slots_index[exam].append(h.index(slot))
    
    # convert to list of lists WARNING: DO NOT EDIT EXAMS AFTER THIS STEP!
    exam_slots = exam_slots.values()
    exam_slots_index = exam_slots_index.values()
    
    # construct room data
    rooms = sorted(set([ room for exam in result_rooms for room in result_rooms[exam] if room in room_capacity]))
    c = [int(room_capacity[room]) for room in rooms]
    
    if verbose: print "Number of rooms", len(rooms)    
    
    if verbose: print sorted(set([ room for exam in result_rooms for room in result_rooms[exam] if room not in room_capacity]))
    
    # For each exam get all rooms at the eligible campus
    exam_rooms = get_exam_rooms(exams, result_rooms, room_campus_id)
    
    # convert to index notation
    for exam in exam_rooms:
        exam_rooms[exam] = [ rooms.index(room) for room in exam_rooms[exam] ]
    exam_rooms = exam_rooms.values()
        
    # Load locking rooms from table
    room_locking_times = read_locked_rooms(semester, rooms, h)
    
    # construct time data. If we dont plan the exam then we lock the room.
    locking_times = defaultdict(list)
    for k, room in enumerate(rooms):
        locking_times[k] = room_locking_times[k]
        for exam in [e for e in result_times if e not in exams]:
            if exam in result_rooms and room in result_rooms[exam]:
                l = h.index(result_times[exam])
                if l not in locking_times[k]:
                    locking_times[k].append(l)
                    
                    
        #for exam in result_times:
            #if exam not in exams and exam in result_rooms and room in result_rooms[exam]:
                #l = h.index(result_times[exam])
                #if l not in locking_times[k]:
                    #locking_times[k].append(l)
                    
    if verbose: print "Locking times", sum( len(locking_times[k]) for k in range(len(rooms)) )
    
    # read conflict data from tumonline
    Q, conflicts, K = read_conflicts(semester, exams = exams, threshold = threshold)
    
    if verbose: print "Mean number of conflicts", np.mean([ len(conflicts[i]) for i, e in enumerate(exams)])
    if verbose: print "Percentage of conflicts", 100.*len(K)/(len(exams)**2)
    
    data = {}
    
    data['n'] = len(s)
    data['r'] = len(c)
    data['p'] = len(h)
    
    data['h'] = h
    data['s'] = s
    data['c'] = c
#TODO: Dont really know how to use it:
#    data['K'] = K
    
    data['conflicts'] = conflicts
    data['conflicts'] = defaultdict(list)
    data['conflicts'][0] = []
    data['locking_times'] = locking_times
    
    data['data_version'] = semester
    data['exam_names'] = exams
    data['exam_slots'] = exam_slots
    data['exam_slots_index'] = exam_slots_index
    data['exam_rooms'] = exam_rooms
    
    data['result_times'] = result_times
    data['result_dates'] = result_dates
    data['result_rooms'] = result_rooms
    data['room_names'] = rooms
    
    return data


if __name__ == "__main__":
    
    data = read_data(semester = "15W", threshold = 0, make_intersection=True, pre_year_data = False, verbose=True, max_periods = 10)
    
    print "n, r, p"
    print data['n'], data['r'], data['p']
    print "KEYS:", [key for key in data]
    
    n = data['n']
    Q = data['Q']
    #print data['exam_slots']
    counter = 0
    conflicts = 0
    
    for i in range(n):
        for j in range(n):
            counter += 1
            if Q[i][j] == 1:
                conflicts += 1
    print "Conflict ratio:", conflicts * 1. / counter
