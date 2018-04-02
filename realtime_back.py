#!/usr/bin/python
from select import select
import subprocess
import os
import signal
import itertools
import threading
import shlex
import sys
import time

def start_fio(path, storage):
    fio_process = subprocess.Popen(['fio', '--minimal', '--eta=0', '--status-interval=1', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, preexec_fn=os.setpgrp)
    exit_code = [None]
    parsing_thread = threading.Thread(target=lambda: parse_fio_output(storage[0]['all'], storage[1]['all'], storage[2]['all'], storage[3]['all'], storage[4]['all'], storage[5]['all'], storage[0]['job_vals'], storage[1]['job_vals'], storage[2]['job_vals'], storage[3]['job_vals'], storage[4]['job_vals'], storage[5]['job_vals'], fio_process, get_jobs(path), exit_code), args=())
    return parsing_thread

def parse_fio_output(riops, rbw, rlat, wiops, wbw, wlat, job_riops, job_rbw, job_rlat, job_wiops, job_wbw, job_wlat, fio_process, numjobs, exit_var):
    cur_job = 0
    while fio_process.poll() == None:
        try:
            if cur_job < numjobs:
                split = fio_process.stdout.readline().split(';')
                job_riops[cur_job].append(int(split[7]))
                job_rbw[cur_job].append(int(split[6]))
                job_rlat[cur_job].append(float(split[15]))
                job_wiops[cur_job].append(int(split[48]))
                job_wbw[cur_job].append(int(split[47]))
                job_wlat[cur_job].append(float(split[56]))
                cur_job+=1
            elif cur_job == numjobs:
                cur_job = 0
                riops_tot = 0
                rbw_tot = 0
                rlat_tot = 0
                wiops_tot = 0
                wbw_tot = 0
                wlat_tot = 0

                for i in range(0, numjobs):
                    riops_tot+=job_riops[i][-1]
                    rbw_tot+=job_rbw[i][-1]
                    rlat_tot+=job_rlat[i][-1]
                    wiops_tot+=job_wiops[i][-1]
                    wbw_tot+=job_wbw[i][-1]
                    wlat_tot+=job_wlat[i][-1]
                riops.append(riops_tot)
                rbw.append(rbw_tot)
                rlat.append(rlat_tot)
                wiops.append(wiops_tot)
                wbw.append(wbw_tot)
                wlat.append(wlat_tot)

        except IndexError:
            poll_res = fio_process.poll()
            if poll_res != None:
                exit_var[0] = poll_res
                return poll_res

def get_jobs(path):
    if path.endswith('ini'):
        cmds = subprocess.Popen(['fio', '--showcmd', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].decode('utf-8').split(' --')
        for cmd in cmds:
            if cmd.startswith('numjobs'):
                return int(cmd.split('=')[1])