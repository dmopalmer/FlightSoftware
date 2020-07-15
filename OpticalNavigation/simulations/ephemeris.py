"""
The purpose of this script is to extend ephemerides that were sampled
at every hour to desired interval.

The 1-hour samples were generating using JPL's HORIZONS program:
https://ssd.jpl.nasa.gov/horizons.cgi#top

Spacecraft coordinate frame is: https://help.agi.com/stk/11.0.1/Content/attitude/attTypes_nadirEci.htm#:~:text=Nadir%20Alignment%20with%20ECI%20Velocity%20Constraint%20Attitude%20Profile,offset%20about%20the%20nadir%20vector.
+X = FORWARD (body frame)
+Z = NADIR (body frame)

Legend: 
Dashed-black arrow: velocity vector (Forward)
Dashed-Red arrow: Rotated X basis vector (using quaternion mult)
Dashed-Green arrow: Rotated Y basis vector (using quaternion mult)
Dashed-Blue arrow: Rotated Z basis vector (using quaternion mult)
Solid-Red arrow: Rotated X basis vector (using attitude matrix)
Solid-Green arrow: Rotated Y basis vector (using attitude matrix)
Solid-Blue arrow: Rotated Z basis vector (using attitude matrix)

Eashaan Kumar, ek485
Summer 2020
"""

import pandas as pd
import numpy as np
import math
import os
from tqdm import tqdm
from animations import LiveMultipleTrajectoryPlot
import argparse

def quaternion_multiply(quaternion1, quaternion0):
    """
    Hamiltonian Product
    Source: https://stackoverflow.com/questions/39000758/how-to-multiply-two-quaternions-by-python-or-numpy
    https://math.stackexchange.com/questions/40164/how-do-you-rotate-a-vector-by-a-unit-quaternion
    ai + bj + ck + d
    """
    x0, y0, z0, w0 = quaternion0
    x1, y1, z1, w1 = quaternion1
    assert abs(np.linalg.norm(quaternion0) - 1) < 1e-6
    assert abs(np.linalg.norm(quaternion1) - 1) < 1e-6
    return np.array([-x1 * x0 - y1 * y0 - z1 * z0 + w1 * w0,
                     x1 * w0 + y1 * z0 - z1 * y0 + w1 * x0,
                     -x1 * z0 + y1 * w0 + z1 * x0 + w1 * y0,
                     x1 * y0 - y1 * x0 + z1 * w0 + w1 * z0], dtype=np.float64)

def attitudeMatrix(quaternion):
    q1, q2, q3, q4 = quaternion
    i, j, k, r = q1, q2, q3, q4
    s = 1.0/(np.linalg.norm(q)**2)
    # return np.array([[q1**2-q2**2-q3**2+q4**2, 2*(q1*q2+q3*q4), 2*(q1*q3-q2*q4)], 
    #                  [2*(q2*q1+q3*q4), -q1**2+q2**2-q3**2+q4**2, 2*(q2*q3-q1*q4)], 
    #                  [2*(q3*q1-q2*q4), 2*(q3*q2-q1*q4), -q1**2-q2**2+q3**2+q4**2]], dtype=np.float64)
    return np.array([[1-2*s*(j**2+k**2), 2*s*(i*j-k*r), 2*s*(i*k+j*r)], 
                     [2*s*(i*j+k*r), 1-2*s*(i*i+k*k), 2*s*(j*k-i*r)], 
                     [2*s*(i*k-j*r), 2*s*(j*k+i*r), 1-2*s*(i*i+j*j)]], dtype=np.float64)



def getRotatedVector(local_vector, q):
    q_1 = [-q[0], -q[1], -q[2], q[3]]
    q_norm = math.sqrt(q_1[0]**2 + q_1[1]**2 + q_1[2]**2 + q_1[3]**2)
    q_1 = [q_1[0]/q_norm, q_1[1]/q_norm, q_1[2]/q_norm, q_1[3]/q_norm]
    a = quaternion_multiply(q, local_vector) # drop the w component
    b = quaternion_multiply(a,q_1)
    assert abs(np.linalg.norm(a) - 1) < 1e-3
    assert abs(np.linalg.norm(b) - 1) < 1e-3
    return b[:3]

def isOrthogonal(a, b):
    err = abs((a*b).sum())
    return [err < 1e-3, err]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-m", "--opnavdataset", help = "path to OpNav Dataset root folder")
    args = vars(ap.parse_args())

    INITIAL_TRAJ_PATH = os.path.join(args['opnavdataset'], 'trajectory', 'traj.csv')
    INITIAL_ATT_PATH = os.path.join(args['opnavdataset'], 'attitude', 'attitude.csv')
    SAMPLED_MOON_PATH = os.path.join(args['opnavdataset'], 'ephemeris', 'sampled_moon_eph.csv')
    SAMPLED_SUN_PATH = os.path.join(args['opnavdataset'], 'ephemeris', 'sampled_sun_eph.csv')

    moonDf = pd.read_csv(SAMPLED_MOON_PATH)
    # sunDf = pd.read_csv(SAMPLED_SUN_PATH)
    trajDf = pd.read_csv(INITIAL_TRAJ_PATH)
    attDf = pd.read_csv(INITIAL_ATT_PATH)

    minX = min([np.min(moonDf['x'].values), np.min(trajDf['x'].values)])
    minY = min([np.min(moonDf['y'].values), np.min(trajDf['y'].values)])
    minZ = min([np.min(moonDf['z'].values), np.min(trajDf['z'].values)])

    maxX = max([np.max(moonDf['x'].values), np.max(trajDf['x'].values)])
    maxY = max([np.max(moonDf['y'].values), np.max(trajDf['y'].values)])
    maxZ = max([np.max(moonDf['z'].values), np.max(trajDf['z'].values)])

    minB = min(minX, minY, minZ)
    maxB = max(maxX, maxY, maxZ)

    liveTraj = LiveMultipleTrajectoryPlot(trajectories=3, trackingArrows=7, bounds=[minX, maxX, minY, maxY, minZ, maxZ])
    # liveTraj.setSimulationBounds(minX, maxX, minY, maxY, minZ, maxZ)
    liveTraj.setTrajectorySettings(0, color='red', label='moon 1 min', alpha=0.5, ls=':')
    # liveTraj.setTrajectorySettings(1, color='yellow', label='sun 1 min', alpha=0.5, ls=":")
    liveTraj.setTrajectorySettings(1, color='green', label='sat 1 min', alpha=0.5, ls=':')
    liveTraj.setTrajectorySettings(2, color=None, label=None, alpha=None, ls=None)
    liveTraj.setTraceLimit(0, 100)
    # liveTraj.setTraceLimit(1, 100)
    # liveTraj.setTraceLimit(2, 100)
    liveTraj.setLeadingBlob(0, size=5, shape='o', color='red', alpha=0.75, label='The Moon')
    # liveTraj.setLeadingBlob(1, size=40, shape='o', color='yellow', alpha=0.75, label='The Sun')
    liveTraj.setLeadingBlob(1, size=10, shape='$L$', color='green', alpha=0.75, label='CisLunar Explorer')
    liveTraj.setLeadingBlob(2, size=20, shape='o', color='blue', alpha=0.75, label='The Earth')

    liveTraj.setTrackingArrowSettings(0, style="-|>", color="r", lw=1, ls='dashed')
    liveTraj.setTrackingArrowSettings(1, style="-|>", color="g", lw=1, ls='dashed')
    liveTraj.setTrackingArrowSettings(2, style="-|>", color="b", lw=1, ls='dashed')
    liveTraj.setTrackingArrowSettings(3, style="-|>", color="r", lw=1, ls='-')
    liveTraj.setTrackingArrowSettings(4, style="-|>", color="g", lw=1, ls='-')
    liveTraj.setTrackingArrowSettings(5, style="-|>", color="b", lw=1, ls='-')
    liveTraj.setTrackingArrowSettings(6, style="-|>", color="black", lw=1, ls='dashed')

    # Earth doesn't move
    liveTraj.updateTraj(2, 0, 0, 0)

    for index, row in moonDf.iterrows():
        # print(moonDf['x'][index], sunDf['x'][index])
        if index % (60) == 0: # sample at hour interval
            liveTraj.updateTraj(0, moonDf['x'][index], moonDf['y'][index], moonDf['z'][index])
            # liveTraj.updateTraj(1, sunDf['x'][index], sunDf['y'][index], sunDf['z'][index])
            liveTraj.updateTraj(1, trajDf['x'][index], trajDf['y'][index], trajDf['z'][index])
            start_pos = np.array([trajDf['x'][index], trajDf['y'][index], trajDf['z'][index]])
            # Velocity
            new_vector = np.array([trajDf['vx'][index], trajDf['vy'][index], trajDf['vz'][index]])
            new_vector /= np.linalg.norm(new_vector)
            liveTraj.updateAtt(6, start_pos, new_vector)

            # Extract quaternions
            q = np.array([attDf['q1'][index], attDf['q2'][index],attDf['q3'][index],attDf['q4'][index]])
            assert abs(np.linalg.norm(q) - 1) < 1e-3
            Aq = attitudeMatrix(q)

            # X axis of spacecraft
            local_vector = np.array([1, 0, 0, 0]) # last 0 is padding
            X_qm = getRotatedVector(local_vector, q.copy())
            X_A = np.dot(Aq,local_vector[:3].T.reshape(3,1))

            # assert abs(np.linalg.norm(X_qm) - 1) < 1e-6
            # assert abs(np.linalg.norm(X_A) - 1) < 1e-3

            # Y axis of spacecraft
            local_vector = np.array([0, 1, 0, 0]) # last 0 is padding
            Y_qm = getRotatedVector(local_vector, q.copy())
            Y_A = np.dot(Aq,local_vector[:3].T.reshape(3,1))

            # assert abs(np.linalg.norm(Y_qm) - 1) < 1e-6
            # assert abs(np.linalg.norm(Y_A) - 1) < 1e-3

            # Z axis of spacecraft
            local_vector = np.array([0, 0, 1, 0]) # last 0 is padding
            Z_qm = getRotatedVector(local_vector, q.copy())
            Z_A = np.dot(Aq,local_vector[:3].T.reshape(3,1))

            # assert abs(np.linalg.norm(Z_qm) - 1) < 1e-6
            # assert abs(np.linalg.norm(Z_A) - 1) < 1e-3

            # XYZ should be orthonormal
            print(isOrthogonal(X_A, Y_A)[1], isOrthogonal(X_A, Z_A)[1], isOrthogonal(Y_A, Z_A)[1])
            # print(isOrthogonal(X_qm, Y_qm)[1], isOrthogonal(X_qm, Z_qm)[1], isOrthogonal(Y_qm, Z_qm)[1])
            assert isOrthogonal(X_A, Y_A)[0] and isOrthogonal(X_A, Z_A)[0] and isOrthogonal(Y_A, Z_A)[0] 
            # assert isOrthogonal(X_qm, Y_qm)[0] and isOrthogonal(X_qm, Z_qm)[0] and isOrthogonal(Y_qm, Z_qm)[0]

            # liveTraj.updateAtt(0, start_pos, X_qm)
            # liveTraj.updateAtt(1, start_pos, Y_qm)
            # liveTraj.updateAtt(2, start_pos, Z_qm)
            liveTraj.updateAtt(3, start_pos, X_A/np.linalg.norm(X_A))
            liveTraj.updateAtt(4, start_pos, Y_A/np.linalg.norm(Y_A))
            liveTraj.updateAtt(5, start_pos, Z_A/np.linalg.norm(Z_A))


            liveTraj.renderUKF(text="{}/{}".format(index,len(moonDf.index)),delay=0.01)

