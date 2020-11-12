from math import pi
import time
from random import uniform as r_uni

import pandas as pd
import numpy as np
import odrive
from odrive.enums import *

import robo
import calibrate
import configure
import trajectory

### DESCONTAR EL TIMEPO X OPERACION EN CADA UNA
traj = trajectory.build_trajectory(pos1=0, pos2=pi, t1=0.5, t2=0.5, res=100)
samples = 100
num_individuals = 5
num_generations = 1

def evo_gains(odrv):

    robo.update_time_errors(odrv, samples)

    class Individual:
        def __init__(self, generation, id, gains):
            self.generation = generation
            self.id = generation*1000+id
            self.gains = gains
            self.error = get_error_score(odrv, gains, traj)

    population = []
    #Initiate population randomly
    for n in range(1, num_individuals+1):
        population.append(Individual(0, n, (r_uni(10,70), r_uni(1/10,3/10), r_uni(0,.75))))

    configure.gains(odrv)

def get_error_score(odrv, gains, traj):
    configure.gains(odrv, *gains)
    ok = 1 #test_vibration()
    if ok:
        t_df = pd.Series(data=performance_traj(odrv, traj, samples))
        error = sum(np.square(np.subtract(t_df.at["input_pos"],t_df.at["pos_estimate_a0"]))) + sum(np.square(np.subtract(t_df.at["input_pos"],t_df.at["pos_estimate_a1"])))
        print(error)
    else:
        error = 0
    return error


def performance_traj(odrv, traj, samples=0):
    if samples == 0:
        sample_interval = 1
    else:
        sample_interval = (len(traj["OUTBOUND"])+len(traj["RETURN"]))//samples
    out_time = traj["OUT_PERIOD"]
    ret_time = traj["RET_PERIOD"]
    sample_diff = len(traj["OUTBOUND"])%sample_interval

    inputs = []
    estimates_a0 = []
    estimates_a1 = []
    currents_a0 = []
    currents_a1 = []

    directions = (traj["OUTBOUND"], traj["RETURN"])

    start = time.perf_counter()
    for d_traj in directions:
        if d_traj== traj["OUTBOUND"]:
            T_time = traj["OUT_PERIOD"]
        else:
            T_time = traj["RET_PERIOD"]

        for i, p in enumerate(d_traj):
            odrv.axis0.controller.input_pos = p
            odrv.axis1.controller.input_pos = p
            if ((i-1)%sample_interval == sample_interval-1):
                inputs.append(p)
                estimates_a0.append(odrv.axis0.encoder.pos_estimate)
                currents_a0.append(odrv.axis0.motor.current_control.Iq_setpoint)
                estimates_a1.append(odrv.axis1.encoder.pos_estimate)
                currents_a1.append(odrv.axis1.motor.current_control.Iq_setpoint)
                time.sleep(float(T_time-robo.input_sleep_adjust-robo.data_delay))
            else:
                time.sleep(float(T_time-robo.input_sleep_adjust))
    end = time.perf_counter()
    print("TRAYECTORY TIME = " + str(end-start))
    return {"input_pos":inputs,
    "pos_estimate_a0":estimates_a0,
    "pos_estimate_a1":estimates_a1,
    "Iq_setpoint_a0":currents_a0,
    "Iq_setpoint_a1":currents_a1}

'''
def build_evo_raw():
    df = pd.DataFrame()
    # Create columns to store data
    df.insert(0, "Individuo", pd.Series([], dtype=int))
    df.insert(1, "pos_gain", pd.Series([], dtype=float))
    df.insert(2, "vel_gain", pd.Series([], dtype=float))
    df.insert(3, "vel_integrator_gain", pd.Series([], dtype=float))
    df.insert(4, "input_pos", pd.Series([], dtype=object))
    df.insert(5, "pos_estimate_a0", pd.Series([], dtype=object))
    df.insert(6, "pos_estimate_a1", pd.Series([], dtype=object))
    df.insert(7, "Iq_setpoint_a0", pd.Series([], dtype=object))
    df.insert(8, "Iq_setpoint_a1", pd.Series([], dtype=object))
    return df

def add_evo_raw(df, id, kp, kv, kvi, inputs, e0, e1, c1, c2):
    row = [id, kp, kv, kvi, inputs, e0, e1, c1, c2
    df.loc[len(df)] = row
    return df
'''
