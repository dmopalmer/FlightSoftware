from OpticalNavigation.core.const import AttitudeStateVector, CameraMeasurementVector, CameraParameters, CameraRecordingParameters, CovarianceMatrix, EphemerisVector, GyroVars, ImageDetectionCircles, MainThrustInfo, QuaternionVector, TrajUKFConstants, TrajectoryStateVector
from utils.constants import OPNAV_INTERVAL
from OpticalNavigation.core.acquisition import startAcquisition, readOmega
from OpticalNavigation.core.cam_meas import cameraMeasurements
import OpticalNavigation.core.ukf as traj_ukf
import OpticalNavigation.core.attitude as attitude
from OpticalNavigation.core.sense import select_camera, record_video, record_gyro
from OpticalNavigation.core.preprocess import extract_frames
from OpticalNavigation.core.find_with_contours import *
from OpticalNavigation.core.const import OPNAV_EXIT_STATUS, CisLunarCameraParameters, CisLunarCamRecParams
import numpy as np
import traceback
import pandas as pd
from utils.db import create_sensor_tables_from_path, OpNavTrajectoryStateModel, OpNavAttitudeStateModel
from utils.db import OpNavEphemerisModel, OpNavCameraMeasurementModel, OpNavPropulsionModel, OpNavGyroMeasurementModel, RebootsModel
from utils.constants import DB_FILE
from utils.log import *
from datetime import datetime, timedelta
import math
from sqlalchemy import desc
from sqlalchemy.orm import session
import re
import glob

logger = get_log()

"""
Entry point into OpNav. This method calls observe() and process().
"""
####### helper functions #######
def __get_covariance_matrix_from_state(state_entry) -> CovarianceMatrix:
    """
    Obtains 6x6 covariance matrix from state entry. Column names should be in the following format:
    r#c# where 1 <= # <= 6
    """
    a_P = [
        [state_entry.r1c1, state_entry.r1c2, state_entry.r1c3, state_entry.r1c4, state_entry.r1c5, state_entry.r1c6],
        [state_entry.r2c1, state_entry.r2c2, state_entry.r2c3, state_entry.r2c4, state_entry.r2c5, state_entry.r2c6],
        [state_entry.r3c1, state_entry.r3c2, state_entry.r3c3, state_entry.r3c4, state_entry.r3c5, state_entry.r3c6],
        [state_entry.r4c1, state_entry.r4c2, state_entry.r4c3, state_entry.r4c4, state_entry.r4c5, state_entry.r4c6],
        [state_entry.r5c1, state_entry.r5c2, state_entry.r5c3, state_entry.r5c4, state_entry.r5c5, state_entry.r5c6],
        [state_entry.r6c1, state_entry.r6c2, state_entry.r6c3, state_entry.r6c4, state_entry.r6c5, state_entry.r6c6],
    ]
    return CovarianceMatrix(matrix=np.array(a_P, dtype=np.float).reshape(6,6))

def __process_propulsion_events(session: session.Session) -> OPNAV_EXIT_STATUS:
    """
    Processes propulsion events (if there are any) using the trajectory ukf.
    [session]: db session
    @return
    opnav_exit_status
    """
    entries = session.query(OpNavPropulsionModel).all()
    num_entries = len(entries)
    logger.info("[OPNAV]: process propulsion...")
    for entry_index, entry in enumerate(entries):
        logger.info(f'[OPNAV]: propulsion event: {entry_index+1}/{num_entries}')
        logger.info(f'[OPNAV]: ----------PROPULSION EVENT----------')
        logger.info(entry)
        exit_status = __process_propulsion(session, entry)
        if exit_status is not OPNAV_EXIT_STATUS.SUCCESS:
            return exit_status
        logger.info(f'[OPNAV] -------------------------------------')
    # clear table
    try:
        num_rows_deleted = session.query(OpNavPropulsionModel).delete()
        session.commit()
        assert num_entries == num_rows_deleted
        return OPNAV_EXIT_STATUS.SUCCESS
    except:
        session.rollback()
        return OPNAV_EXIT_STATUS.FAILURE

def __closest(session: session.Session, ts, model):
    """
    Searches for closest ephemeris based on time [ts]
    https://stackoverflow.com/questions/42552696/sqlalchemy-nearest-datetime
    @return
    closest ephemeris entry
    """
    # find the closest events which are greater/less than the timestamp
    gt_event = session.query(model).filter(model.time_retrieved >= ts).order_by(model.time_retrieved.asc()).first()
    lt_event = session.query(model).filter(model.time_retrieved < ts).order_by(model.time_retrieved.desc()).first()

    # find diff between events and the ts, if no event found default to infintiy
    gt_diff = (gt_event.time_retrieved - ts).total_seconds() if gt_event else math.inf
    lt_diff = (ts - lt_event.time_retrieved).total_seconds() if lt_event else math.inf

    # return the newest event if it is closer to ts else older event
    # if an event is None its diff will always be greater as we set it to infinity
    return gt_event if gt_diff < lt_diff else lt_event

def __calculate_cam_measurements(body1:np.ndarray, body2:np.ndarray) -> np.float:
    """
    Calculates angular separation between two bodies.
    Source: https://stackoverflow.com/questions/52210911/great-circle-distance-between-two-p-x-y-z-points-on-a-unit-sphere
    @params
    [body1]: spherical coordinates representing circle center of first body, size: (>= 3,), format: (x spherical coord, y spherical coord, z spherical coord)
    [body2]: spherical coordinates representing circle center of second body, size: (>= 3,), format: (x spherical coord, y spherical coord, z spherical coord)
    @return
    angular separation in radians
    """
    d_em = math.sqrt((body1[0]-body2[0])**2+(body1[1]-body2[1])**2+(body1[2]-body2[2])**2)
    return 2 * math.asin(d_em/2)
################################

def start(sql_path=DB_FILE,num_runs=1,gyro_count=4,gyro_vars:GyroVars=GyroVars(), camera_params:CameraParameters=CisLunarCameraParameters) -> OPNAV_EXIT_STATUS:
    """
    Entry point into OpNav System.
    [sql_path]: path to .sqlite file with the SQL prefix
    [num_runs]: number of times observation step is run. Does not include propulsion events
                [num_runs] corresponds to number of trajectory measurements, not attitude measurements
    [gyro_count]: number of gyro measurements taken per observation step
    [gyro_vars]: GyroVars object containing gyroscope properties
    @return
    opnav_exit_status: 0 (success), ...
    """
    assert gyro_count > 1
    create_session = create_sensor_tables_from_path(sql_path)
    session = create_session()
    assert len(session.query(OpNavTrajectoryStateModel).all()) >= 1 and len(session.query(OpNavAttitudeStateModel).all()) >= 1

    propulsion_exit_status = __process_propulsion_events(session)
    if propulsion_exit_status is not OPNAV_EXIT_STATUS.SUCCESS:
        print(f'propulsion processing result: {propulsion_exit_status}')
        # TODO: Handle propulsion processing failure
        return propulsion_exit_status
        
    for run in range(num_runs):
        # process propagation step
        __observe(session, gyro_count)
        propagation_exit_status = __process_propagation(session, gyro_vars, camera_params)
        # TODO: Handle exit status
        if propagation_exit_status is not OPNAV_EXIT_STATUS.SUCCESS:
            print(f'propagation processing result: {propagation_exit_status}')
            return propagation_exit_status

    return OPNAV_EXIT_STATUS.SUCCESS

def __observe(session: session.Session, gyro_count: int, camera_params:CameraParameters=CisLunarCameraParameters, camera_rec_params:CameraRecordingParameters=CisLunarCamRecParams) -> OPNAV_EXIT_STATUS:
    """
    Begin OpNav acquisition and storing process. The system will record videos from
    the three cameras onboard and store them on the SD card as video format. It will
    record gyroscope measurements and store them in a table on the SD card.
    """
    # 1. select camera
    # 2. record camera measurements
    # 3. record gyro measurements
    observeStart = datetime.now()
    recordings = []
    for i in [1, 2, 3]: # These are the hardware IDs of the camera mux ports
        select_camera(id = i)
        logger.info(f"[OPNAV]: Recording from camera {i}")
        # TODO: figure out exposure parameters
        filename_timestamp1 = record_video(f"cam{i}_expLow.mjpeg", framerate = camera_rec_params.fps, recTime=camera_rec_params.recTime, exposure=camera_rec_params.expLow)
        filename_timestamp2 = record_video(f"cam{i}_expHigh.mjpeg", framerate = camera_rec_params.fps, recTime=camera_rec_params.recTime, exposure=camera_rec_params.expHigh)
        recordings.append(filename_timestamp1)
        recordings.append(filename_timestamp2)

    ##### Commented out for software demo
    #logger.info("[OPNAV]: Extracting frames...")
    # TODO: What is format of vid_dir / where is file stored? recordings[i][0]?
    #frames0 = extract_frames(vid_dir=recordings[0][0], endTimestamp = recordings[0][1])
    #frames1 = extract_frames(vid_dir=recordings[1][0], endTimestamp = recordings[1][1])
    #frames2 = extract_frames(vid_dir=recordings[2][0], endTimestamp = recordings[2][1])
    #frames3 = extract_frames(vid_dir=recordings[3][0], endTimestamp = recordings[3][1])
    #frames4 = extract_frames(vid_dir=recordings[4][0], endTimestamp = recordings[4][1])
    #frames5 = extract_frames(vid_dir=recordings[5][0], endTimestamp = recordings[5][1])
    #frames = frames0 + frames1 + frames2 + frames3 + frames4 + frames5
    #####
    # On Stephen's VM: /home/stephen_z/PycharmProjects/FlightSoftware/OpticalNavigation/tests/surrender_images/*.jpg
    # On HITL, path to images will be /home/pi/surrender_images/*.jpg
    #frames = glob.glob("/home/stephen_z/PycharmProjects/FlightSoftware/OpticalNavigation/tests/surrender_images/*.jpg")
    frames = glob.glob("/home/pi/surrender_images/*.jpg")
    logger.info(f"[OPNAV]: Total number of frames is {len(frames)}")

    #These arrays take the form (number if frame number): [[x0,y0,z0,diameter0], [x1,y1,z1,diameter1], ...]
    earthDetectionArray = np.zeros((len(frames), 4), dtype = np.float)
    moonDetectionArray = np.zeros((len(frames), 4), dtype = np.float)
    sunDetectionArray = np.zeros((len(frames), 4), dtype = np.float)
    logger.info("[OPNAV]: Finding...")
    progress = 1
    for f in range(len(frames)):
        logger.info(f"[OPNAV]: Image {progress}/96: {frames[f]}")
        imageDetectionCircles = find(frames[f])# Puts results in ImageDetectionCircles object which is then accessed by next lines
        earthDetectionArray[f, ...] = imageDetectionCircles.get_earth_detection()
        moonDetectionArray[f, ...] = imageDetectionCircles.get_moon_detection()
        sunDetectionArray[f, ...] = imageDetectionCircles.get_sun_detection()
        logger.info(f"[OPNAV]: Result: Earth: {imageDetectionCircles.get_earth_detection()}, Moon: {imageDetectionCircles.get_moon_detection()}, Sun: {imageDetectionCircles.get_sun_detection()}")
        progress += 1


    # best___Tuple is tuple of file, distance and vector of best result

    # Find the distance to center
    logger.info("[OPNAV]: Finding best frames...")
    earthCenterDistances = []
    for e in range(earthDetectionArray.shape[0]):
        dist = math.sqrt(earthDetectionArray[e, 0]**2 + earthDetectionArray[e, 1]**2)
        earthCenterDistances.append(dist)
    earthFileDistVec = list(zip(frames, earthCenterDistances, earthDetectionArray))
    bestEarthTuple = earthFileDistVec[0]
    for e in earthFileDistVec:
        if np.isnan(e[1]):
            continue
        if e[1] < bestEarthTuple[1] or np.isnan(bestEarthTuple[1]):
            bestEarthTuple = e

    moonCenterDistances = []
    for m in range(moonDetectionArray.shape[0]):
        dist = math.sqrt(moonDetectionArray[m, 0]**2 + moonDetectionArray[m, 1]**2)
        moonCenterDistances.append(dist)
    moonFileDistVec = list(zip(frames, moonCenterDistances, moonDetectionArray))
    bestMoonTuple = moonFileDistVec[0]
    for m in moonFileDistVec:
        if np.isnan(m[1]):
            continue
        if m[1] < bestMoonTuple[1] or np.isnan(bestMoonTuple[1]):
            bestMoonTuple = m

    sunCenterDistances = []
    for s in range(sunDetectionArray.shape[0]):
        dist = math.sqrt(sunDetectionArray[s, 0]**2 + sunDetectionArray[s, 1]**2)
        sunCenterDistances.append(dist)
    sunFileDistVec = list(zip(frames, sunCenterDistances, sunDetectionArray))
    bestSunTuple = sunFileDistVec[0]
    for s in sunFileDistVec:
        if np.isnan(s[1]):
            continue
        if s[1] < bestSunTuple[1] or np.isnan(bestSunTuple[1]):
            bestSunTuple = s

    # We now have the best result for earth, moon and sun; time to rotate vectors

    logger.info("[OPNAV]: Performing camera to body rotations...")
    for data in bestEarthTuple, bestMoonTuple, bestSunTuple:
        coordArray = np.array([data[2][0], data[2][1], data[2][2]]).reshape(3, 1)
        camNum = int(re.search("[cam](\d+)", data[0]).group(1))
        if camNum == 1:
            coordArray = (camera_params.cam1Rotation).dot(coordArray)
        elif camNum == 2:
            coordArray = (camera_params.cam2Rotation).dot(coordArray)
        elif camNum == 3:
            coordArray = (camera_params.cam3Rotation).dot(coordArray)
        data[2][0] = coordArray[0]
        data[2][1] = coordArray[1]
        data[2][2] = coordArray[2]

    logger.info("[OPNAV]: Gathering gyro measurements...")
    gyro_meas = record_gyro(count=gyro_count)
    for g in range(gyro_meas.shape[0]):
        omega = gyro_meas[g, ...]
        new_entry = OpNavGyroMeasurementModel(
            time_retrieved=datetime.now(),
            omegax=omega[0],
            omegay=omega[1],
            omegaz=omega[2]
        )
        session.add(new_entry)
    # TODO: Make sure that axes are correct - i.e. are consistent with what UKF expects

    logger.info("[OPNAV]: Body to T0 rotation...")
    avgGyroY = np.mean(gyro_meas, axis = 0)[1] * 180 / math.pi
    # Rotation is product of angular speed and time between frame and start of observation
    lastRebootRow = session.query(RebootsModel).order_by(desc('reboot_at')).first()
    lastReboot = lastRebootRow.reboot_at

    if not np.isnan(bestEarthTuple[1]):
        earthTimestamp = int(re.search("[t](\d+)", bestEarthTuple[0]).group(1))
        dateTimeEarth = lastReboot + timedelta(microseconds=earthTimestamp)
        earthTimeElapsed = (dateTimeEarth - observeStart).total_seconds()
        earthRotation = avgGyroY * earthTimeElapsed
        tZeroEarthRotation = np.array([math.cos(earthRotation), 0, math.sin(earthRotation), 0, 1, 0, -1 * math.sin(earthRotation), 0, math.cos(earthRotation)]).reshape(3, 3)
        coordArray = np.array([bestEarthTuple[2][0], bestEarthTuple[2][1], bestEarthTuple[2][2]]).reshape(3, 1)
        coordArray = tZeroEarthRotation.dot(coordArray)
        bestEarthTuple[2][1] = coordArray[1]
        bestEarthTuple[2][2] = coordArray[2]
        bestEarthTuple[2][0] = coordArray[0]

    if not np.isnan(bestMoonTuple[1]):
        moonTimestamp = int(re.search("[t](\d+)", bestMoonTuple[0]).group(1))
        dateTimeMoon = lastReboot + timedelta(microseconds=moonTimestamp)
        moonTimeElapsed = (dateTimeMoon - observeStart).total_seconds()
        moonRotation = avgGyroY * moonTimeElapsed
        tZeroMoonRotation = np.array([math.cos(moonRotation), 0, math.sin(moonRotation), 0, 1, 0, -1 * math.sin(moonRotation), 0, math.cos(moonRotation)]).reshape(3, 3)
        coordArray = np.array([bestMoonTuple[2][0], bestMoonTuple[2][1], bestMoonTuple[2][2]]).reshape(3, 1)
        coordArray = tZeroMoonRotation.dot(coordArray)
        bestMoonTuple[2][1] = coordArray[1]
        bestMoonTuple[2][2] = coordArray[2]
        bestMoonTuple[2][0] = coordArray[0]

    if not np.isnan(bestSunTuple[1]):
        sunTimestamp = int(re.search("[t](\d+)", bestSunTuple[0]).group(1))
        dateTimeSun = lastReboot + timedelta(microseconds=sunTimestamp)
        sunTimeElapsed = (dateTimeSun - observeStart).total_seconds()
        sunRotation = avgGyroY * sunTimeElapsed
        tZeroSunRotation = np.array([math.cos(sunRotation), 0, math.sin(sunRotation), 0, 1, 0, -1 * math.sin(sunRotation), 0, math.cos(sunRotation)]).reshape(3, 3)
        coordArray = np.array([bestSunTuple[2][0], bestSunTuple[2][1], bestSunTuple[2][2]]).reshape(3, 1)
        coordArray = tZeroSunRotation.dot(coordArray)
        bestSunTuple[2][1] = coordArray[1]
        bestSunTuple[2][2] = coordArray[2]
        bestSunTuple[2][0] = coordArray[0]

    bestDetectedCircles = ImageDetectionCircles()
    bestDetectedCircles.set_earth_detection(bestEarthTuple[2][0], bestEarthTuple[2][1], bestEarthTuple[2][2], bestEarthTuple[2][3])
    bestDetectedCircles.set_moon_detection(bestMoonTuple[2][0], bestMoonTuple[2][1], bestMoonTuple[2][2], bestMoonTuple[2][3])
    bestDetectedCircles.set_sun_detection(bestSunTuple[2][0], bestSunTuple[2][1], bestSunTuple[2][2], bestSunTuple[2][3])
    # As tuples
    best_e = (bestEarthTuple[2][0], bestEarthTuple[2][1], bestEarthTuple[2][2], bestEarthTuple[2][3])
    best_m = (bestMoonTuple[2][0], bestMoonTuple[2][1], bestMoonTuple[2][2], bestMoonTuple[2][3])
    best_s = (bestSunTuple[2][0], bestSunTuple[2][1], bestSunTuple[2][2], bestSunTuple[2][3])
    ######

    logger.info(f"[OPNAV]: Best Earth {best_e}")
    logger.info(f"[OPNAV]: Best Sun {best_s}")
    logger.info(f"[OPNAV]: Best Moon {best_m}")
    # Calculate angular separation
    ang_em = __calculate_cam_measurements(body1=bestDetectedCircles.get_earth_detection(), body2=bestDetectedCircles.get_moon_detection())

    ang_es = __calculate_cam_measurements(body1=bestDetectedCircles.get_earth_detection(), body2=bestDetectedCircles.get_sun_detection())

    ang_ms = __calculate_cam_measurements(body1=bestDetectedCircles.get_moon_detection(), body2=bestDetectedCircles.get_sun_detection())

    # Write measurements to corresponding databases
    new_entry = OpNavCameraMeasurementModel.from_tuples(
        measurement=CameraMeasurementVector(ang_em=ang_em, ang_es=ang_es, ang_ms=ang_ms, e_dia=best_e[3], m_dia=best_m[3], s_dia=best_s[3]),
        time=datetime.now()
    )
    session.add(new_entry)
    session.commit()
    logger.info("[OPNAV]: Observe Complete!")


def __process_propulsion(session: session.Session, propulsion_entry) -> OPNAV_EXIT_STATUS:
    """
    Process propulsion event. Each event has a start and end time for when the thruster
    was fired. The trajectory UKF entends the previous estimate using the dynamics model.
    Thus, only trajectory state db is updated.
    @return
    exit status:
        NO_TRAJECTORY_ENTRY_FOUND: Trajectory db is empty
        NO_ATTITUDE_ENTRY_FOUND: Attitude db is empty
        NO_EPHEMERIS_ENTRY_FOUND: Ephemeris db is empty
        OPNAV_EXIT_STATUS.FAILURE: TODO
        OPNAV_EXIT_STATUS.SUCCESS: otherwise
    """
    # Get latest entry
    init_traj_entry = session.query(OpNavTrajectoryStateModel).order_by(desc('time_retrieved')).first()
    if init_traj_entry is None:
        return OPNAV_EXIT_STATUS.NO_TRAJECTORY_ENTRY_FOUND
    init_att_entry = session.query(OpNavAttitudeStateModel).order_by(desc('time_retrieved')).first()
    if init_att_entry is None:
        return OPNAV_EXIT_STATUS.NO_ATTITUDE_ENTRY_FOUND
    ephemeris_entry = __closest(session, propulsion_entry.time_start, OpNavEphemerisModel)
    if ephemeris_entry is None:
        return OPNAV_EXIT_STATUS.NO_EPHEMERIS_ENTRY_FOUND

    # print(f'\nusing stored state: \n\t{init_traj_entry} \n\t{init_att_entry} \n\t{ephemeris_entry}\n')
    
    quat = QuaternionVector(q1=init_att_entry.q1, q2=init_att_entry.q2, q3=init_att_entry.q3, q4=init_att_entry.q4)
    main_thrust_info = MainThrustInfo(kick_orientation=quat, acceleration_magnitude=propulsion_entry.acceleration)
    dt = (propulsion_entry.time_end-propulsion_entry.time_start).total_seconds()
    sun_eph = EphemerisVector(x_pos=ephemeris_entry.sun_x, y_pos=ephemeris_entry.sun_y, 
                            z_pos=ephemeris_entry.sun_z, x_vel=ephemeris_entry.sun_vx, 
                            y_vel=ephemeris_entry.sun_vy, z_vel=ephemeris_entry.sun_vz)
    moon_eph = EphemerisVector(x_pos=ephemeris_entry.moon_x, y_pos=ephemeris_entry.moon_y, 
                            z_pos=ephemeris_entry.moon_z, x_vel=ephemeris_entry.moon_vx, 
                            y_vel=ephemeris_entry.moon_vy, z_vel=ephemeris_entry.moon_vz)

    traj_state = TrajectoryStateVector(x_pos=init_traj_entry.position_x, y_pos=init_traj_entry.position_y, 
                                    z_pos=init_traj_entry.position_z, x_vel=init_traj_entry.velocity_x, 
                                    y_vel=init_traj_entry.velocity_y, z_vel=init_traj_entry.velocity_z)
    P = __get_covariance_matrix_from_state(init_traj_entry)
    new_est = traj_ukf.runTrajUKF(moon_eph, sun_eph, None, traj_state, dt, P, CisLunarCameraParameters, main_thrust_info, dynamicsOnly=True) 
    # TODO: Figure out how to utilize Kalman Gain (K)
    # update db with new values
    pos = new_est.new_state.get_position_data()
    vel = new_est.new_state.get_velocity_data()
    entries = [
        OpNavTrajectoryStateModel.from_tuples(
            position=(pos[0], pos[1], pos[2]), velocity=(vel[0], vel[1], vel[2]), P=new_est.new_P.data, time=propulsion_entry.time_end)
    ]
    session.bulk_save_objects(entries)
    session.commit()
    # TODO: Check for any failures and return fail status
    logger.info("[OPNAV]: process_propulsion complete!")
    return OPNAV_EXIT_STATUS.SUCCESS
    
def __process_propagation(session:session.Session, gyro_vars:GyroVars, camera_params:CameraParameters) -> OPNAV_EXIT_STATUS:
    """
    Process propagation event. This event does not handle propulsions, so dynamicsModel is set to False in the traj ukf.
    The trajectory UKF and attitude UKF extend satellite's previous position, velocity, attitude (Rodriguez Params and
    quaternion) and bias estimates. Thus, trajectory and attitude state dbs are updated.
    @return
    exit status:
        NO_TRAJECTORY_ENTRY_FOUND: Trajectory db is empty
        NO_ATTITUDE_ENTRY_FOUND: Attitude db is empty
        NO_CAMMEAS_ENTRY_FOUND: Camera measurements db is empty
        NO_GYROMEAS_ENTRY_FOUND: Gyro measurements db is empty
        NO_EPHEMERIS_ENTRY_FOUND: Ephemeris db is empty
        OPNAV_EXIT_STATUS.FAILURE: TODO
        OPNAV_EXIT_STATUS.SUCCESS: otherwise
    """
    # Get latest entry
    init_traj_entry = session.query(OpNavTrajectoryStateModel).order_by(desc('time_retrieved')).first()
    if init_traj_entry is None:
        return OPNAV_EXIT_STATUS.NO_TRAJECTORY_ENTRY_FOUND
    init_att_entry = session.query(OpNavAttitudeStateModel).order_by(desc('time_retrieved')).first()
    if init_att_entry is None:
        return OPNAV_EXIT_STATUS.NO_ATTITUDE_ENTRY_FOUND
    cam_meas_entry = session.query(OpNavCameraMeasurementModel).order_by(desc('time_retrieved')).first()
    if cam_meas_entry is None:
        return OPNAV_EXIT_STATUS.NO_CAMMEAS_ENTRY_FOUND
    gyro_meas_entries = session.query(OpNavGyroMeasurementModel).filter(OpNavGyroMeasurementModel.time_retrieved >= cam_meas_entry.time_retrieved).all()
    if gyro_meas_entries is None or len(gyro_meas_entries) <= 1:
        return OPNAV_EXIT_STATUS.ONE_OR_LESS_GYROMEAS_ENTRIES_FOUND
    ephemeris_entry = __closest(session, cam_meas_entry.time_retrieved, OpNavEphemerisModel)
    if ephemeris_entry is None:
        return OPNAV_EXIT_STATUS.NO_EPHEMERIS_ENTRY_FOUND
    assert cam_meas_entry.time_retrieved >= init_traj_entry.time_retrieved

    # print(f'\nusing stored state: \n\t{init_traj_entry} \n\t{init_att_entry} \n\t{cam_meas_entry} \n\t{gyro_meas_entries} \n\t{ephemeris_entry}\n')

    quat = QuaternionVector(q1=init_att_entry.q1, q2=init_att_entry.q2, q3=init_att_entry.q3, q4=init_att_entry.q4)
    att_state = AttitudeStateVector(rod_param1=init_att_entry.r1, rod_param2=init_att_entry.r2, 
                                    rod_param3=init_att_entry.r3, bias1=init_att_entry.b1, 
                                    bias2=init_att_entry.b2, bias3=init_att_entry.b3)
    prev_state_time = init_traj_entry.time_retrieved
    new_state_time = cam_meas_entry.time_retrieved
    cam_dt = (new_state_time-prev_state_time).total_seconds()
    sun_eph = EphemerisVector(x_pos=ephemeris_entry.sun_x, y_pos=ephemeris_entry.sun_y, 
                            z_pos=ephemeris_entry.sun_z, x_vel=ephemeris_entry.sun_vx, 
                            y_vel=ephemeris_entry.sun_vy, z_vel=ephemeris_entry.sun_vz)
    moon_eph = EphemerisVector(x_pos=ephemeris_entry.moon_x, y_pos=ephemeris_entry.moon_y, 
                            z_pos=ephemeris_entry.moon_z, x_vel=ephemeris_entry.moon_vx, 
                            y_vel=ephemeris_entry.moon_vy, z_vel=ephemeris_entry.moon_vz)
    cam_meas = CameraMeasurementVector(ang_em=cam_meas_entry.ang_em, ang_es=cam_meas_entry.ang_es, ang_ms=cam_meas_entry.ang_ms, e_dia=cam_meas_entry.e_dia, m_dia=cam_meas_entry.m_dia, s_dia=cam_meas_entry.s_dia)
    traj_state = TrajectoryStateVector(x_pos=init_traj_entry.position_x, y_pos=init_traj_entry.position_y, 
                                    z_pos=init_traj_entry.position_z, x_vel=init_traj_entry.velocity_x, 
                                    y_vel=init_traj_entry.velocity_y, z_vel=init_traj_entry.velocity_z)

    traj_P = __get_covariance_matrix_from_state(init_traj_entry)
    att_P = __get_covariance_matrix_from_state(init_att_entry)
    new_est = traj_ukf.runTrajUKF(moon_eph, sun_eph, cam_meas, traj_state, cam_dt, traj_P, camera_params, None, dynamicsOnly=False) 

    pos = new_est.new_state.get_position_data()
    vel = new_est.new_state.get_velocity_data()
    entries = [
        OpNavTrajectoryStateModel.from_tuples(
            position=(pos[0], pos[1], pos[2]), velocity=(vel[0], vel[1], vel[2]), P=new_est.new_P.data, time=cam_meas_entry.time_retrieved)
    ]
    # prepare data for attitude ukf
    actual_gyro_count = len(gyro_meas_entries)

    omegas = np.zeros((actual_gyro_count,3))
    estimatedSatState = np.zeros((actual_gyro_count,3))
    moonPos = np.zeros((actual_gyro_count,3))
    sunPos = np.zeros((actual_gyro_count,3))
    tempSatState = new_est.new_state.data.flatten()
    tempMoonState = moon_eph.data.flatten()
    tempSunState = sun_eph.data.flatten()
    timeline = [0]*actual_gyro_count
    for i,gyro_entry in enumerate(gyro_meas_entries):
        #om = b['gyro_meas'][i]['omega'].flatten()
        #bi = b['gyro_meas'][i]['bias'].flatten()
        omegas[i][0] = gyro_entry.omegax
        omegas[i][1] = gyro_entry.omegay
        omegas[i][2] = gyro_entry.omegaz
        estimatedSatState[i][0] = tempSatState[0]
        estimatedSatState[i][1] = tempSatState[1]
        estimatedSatState[i][2] = tempSatState[2]
        moonPos[i][0] = tempMoonState[0]
        moonPos[i][1] = tempMoonState[1]
        moonPos[i][2] = tempMoonState[2]
        sunPos[i][0] = tempSunState[0]
        sunPos[i][1] = tempSunState[1]
        sunPos[i][2] = tempSunState[2]
        if i > 0:
            timeline[i] = (gyro_entry.time_retrieved-gyro_meas_entries[i-1].time_retrieved).total_seconds() # num seconds elapsed since previous gyro measurement
    
    # Attitude ukf expects gyro sample rate. Since the rate isn't fixed, we pass in the average time elapsed between each measurement for the first measurement.
    timeline[0] = sum(timeline)/(actual_gyro_count-1.) 
    gyroVars = (gyro_vars.gyro_sigma, gyro_vars.gyro_sample_rate, gyro_vars.get_Q_matrix(), gyro_vars.get_R_matrix())
    newAttOut = attitude.runAttitudeUKF(cam_dt, 
                                    gyroVars, 
                                    att_P, 
                                    att_state, 
                                    quat, 
                                    omegas, 
                                    estimatedSatState, 
                                    moonPos, 
                                    sunPos, 
                                    timeline)
    new_quat = newAttOut.new_quat
    new_rod_params = newAttOut.new_state.get_rod_params()
    new_biases = newAttOut.new_state.get_biases()
    entries.extend([
        OpNavAttitudeStateModel.from_tuples(
            quat=(new_quat.get_q1(), new_quat.get_q2(), new_quat.get_q3(), new_quat.get_q4()), 
            rod_params=(new_rod_params[0], new_rod_params[1], new_rod_params[2]), 
            biases=(new_biases[0], new_biases[1], new_biases[2]), 
            P=newAttOut.new_P.data, time=gyro_meas_entries[-1].time_retrieved) # new attitude state time set to last gyro measurement time
    ])
    session.bulk_save_objects(entries)
    session.commit()
    # TODO: Check for any failures and return fail status
    logger.info("[OPNAV]: process_propagation complete!")
    return OPNAV_EXIT_STATUS.SUCCESS
