from numpy.testing._private.utils import measure
from sys import float_repr_style
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import Float, DateTime, Boolean
from sqlalchemy.dialects import postgresql

from OpticalNavigation.core.const import CameraMeasurementVector
from drivers.power.power_structs import eps_hk_t

create_session = sessionmaker()

# declarative_base for WalletModel used by WalletManager
SQLAlchemyTableBase = declarative_base()

# NOTE do not use foreign key in any of these tables
# TODO implement Model classes for all sensor data to be stored


class CommandModel(SQLAlchemyTableBase):
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True)
    command_received = Column(DateTime)
    name = Column(String)
    app_code = Column(Integer)
    opcode = Column(Integer)
    executed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<CommandModel(Name={self.name}, app_code={self.app_code}, " \
               f"opcode={self.opcode} executed_at=" \
               f"{str(self.executed_at) if self.executed_at is not None else 'NE'})>"


class PressureModel(SQLAlchemyTableBase):
    __tablename__ = "pressure"

    id = Column(Integer, primary_key=True)
    measurement_taken = Column(DateTime)
    pressure = Column(Float)

    def __repr__(self):
        return (f"<PressureModel(pressure={self.pressure}, "
                f"taken_at={str(self.measurement_taken)})>")


class ThermocoupleModel(SQLAlchemyTableBase):
    __tablename__ = "thermocouple"

    id = Column(Integer, primary_key=True)
    measurement_taken = Column(DateTime)
    pressure = Column(Float)


class RTCModel(SQLAlchemyTableBase):
    __tablename__ = "rtc"

    id = Column(Integer, primary_key=True)
    measurement_taken = Column(DateTime)
    time_retrieved = Column(DateTime)

    def __repr__(self):
        return (f"<RTCModel(TimeRetrieved={str(self.time_retrieved)}, "
                f"taken_at={str(self.time_retrieved)})>")


class OpNavTrajectoryStateModel(SQLAlchemyTableBase):
    __tablename__ = "opnav_trajectory_state"

    id = Column(Integer, primary_key=True)
    time_retrieved = Column(DateTime)
    position_x = Column(Float)
    position_y = Column(Float)
    position_z = Column(Float)
    velocity_x = Column(Float)
    velocity_y = Column(Float)
    velocity_z = Column(Float)
    # Covariance Matrix
    r1c1, r1c2, r1c3, r1c4, r1c5, r1c6 = Column(Float), Column(Float), Column(Float), Column(Float), Column(Float), Column(Float)
    r2c1, r2c2, r2c3, r2c4, r2c5, r2c6 = Column(Float), Column(Float), Column(Float), Column(Float), Column(Float), Column(Float)
    r3c1, r3c2, r3c3, r3c4, r3c5, r3c6 = Column(Float), Column(Float), Column(Float), Column(Float), Column(Float), Column(Float)
    r4c1, r4c2, r4c3, r4c4, r4c5, r4c6 = Column(Float), Column(Float), Column(Float), Column(Float), Column(Float), Column(Float)
    r5c1, r5c2, r5c3, r5c4, r5c5, r5c6 = Column(Float), Column(Float), Column(Float), Column(Float), Column(Float), Column(Float)
    r6c1, r6c2, r6c3, r6c4, r6c5, r6c6 = Column(Float), Column(Float), Column(Float), Column(Float), Column(Float), Column(Float)

    """
    Create an OpNavTrajectoryStateModel instance
    @params
    [position]: position coordiantes tuple in J2000 ECI coordinates (km): (x, y, z)
    [velocity]: velocity coordiantes tuple in J2000 ECI coordinates (km/s): (vx, vy, vz)
    [P]: covariance matrix output (6x6 numpy matrix)
    [time]: mission time of the measurements when trajectory quantities were calculated
    """

    @staticmethod
    def from_tuples(position, velocity, P, time):
        position_x, position_y, position_z = position
        velocity_x, velocity_y, velocity_z = velocity
        return OpNavTrajectoryStateModel(
            time_retrieved=time,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
            velocity_z=velocity_z,
            position_x=position_x,
            position_y=position_y,
            position_z=position_z,
            r1c1 = P[0,0], r1c2 = P[0,1], r1c3 = P[0,2], r1c4 = P[0,3], r1c5 = P[0,4], r1c6 = P[0,5],
            r2c1 = P[1,0], r2c2 = P[1,1], r2c3 = P[1,2], r2c4 = P[1,3], r2c5 = P[1,4], r2c6 = P[1,5],
            r3c1 = P[2,0], r3c2 = P[2,1], r3c3 = P[2,2], r3c4 = P[2,3], r3c5 = P[2,4], r3c6 = P[2,5],
            r4c1 = P[3,0], r4c2 = P[3,1], r4c3 = P[3,2], r4c4 = P[3,3], r4c5 = P[3,4], r4c6 = P[3,5],
            r5c1 = P[4,0], r5c2 = P[4,1], r5c3 = P[4,2], r5c4 = P[4,3], r5c5 = P[4,4], r5c6 = P[4,5],
            r6c1 = P[5,0], r6c2 = P[5,1], r6c3 = P[5,2], r6c4 = P[5,3], r6c5 = P[5,4], r6c6 = P[5,5],
        )

    def __repr__(self):
        return (
            f"<OpNavTrajectoryStateModel(TimeRetrieved=({str(self.time_retrieved)}"
            f", velocity=({self.velocity_x}, {self.velocity_y}, "
            f"{self.velocity_z}), position=({self.position_x}, "
            f"{self.position_y}, {self.position_z}), "
            f"covariance matrix trace=({self.r1c1+self.r2c2+self.r3c3+self.r4c4+self.r5c5+self.r6c6}))>"
        )

class OpNavAttitudeStateModel(SQLAlchemyTableBase):
    __tablename__ = "opnav_attitude_state"

    id = Column(Integer, primary_key=True)
    time_retrieved = Column(DateTime)
    q1 = Column(Float)
    q2 = Column(Float)
    q3 = Column(Float)
    q4 = Column(Float)
    r1 = Column(Float)
    r2 = Column(Float)
    r3 = Column(Float)
    b1 = Column(Float)
    b2 = Column(Float)
    b3 = Column(Float)
    # Covariance Matrix
    r1c1, r1c2, r1c3, r1c4, r1c5, r1c6 = Column(Float), Column(Float), Column(Float), Column(Float), Column(Float), Column(Float)
    r2c1, r2c2, r2c3, r2c4, r2c5, r2c6 = Column(Float), Column(Float), Column(Float), Column(Float), Column(Float), Column(Float)
    r3c1, r3c2, r3c3, r3c4, r3c5, r3c6 = Column(Float), Column(Float), Column(Float), Column(Float), Column(Float), Column(Float)
    r4c1, r4c2, r4c3, r4c4, r4c5, r4c6 = Column(Float), Column(Float), Column(Float), Column(Float), Column(Float), Column(Float)
    r5c1, r5c2, r5c3, r5c4, r5c5, r5c6 = Column(Float), Column(Float), Column(Float), Column(Float), Column(Float), Column(Float)
    r6c1, r6c2, r6c3, r6c4, r6c5, r6c6 = Column(Float), Column(Float), Column(Float), Column(Float), Column(Float), Column(Float)

    """
    Create an OpNavAttitudeStateModel instance
    @params
    [position]: position coordiantes tuple in J2000 ECI coordinates (km): (x, y, z)
    [velocity]: velocity coordiantes tuple in J2000 ECI coordinates (km/s): (vx, vy, vz)
    [P]: covariance matrix output (6x6 numpy matrix)
    [time]: mission time of the measurements when attitude quantities were calculated
    """
    @staticmethod
    def from_tuples(quat, rod_params, biases, P, time):
        q1, q2, q3, q4 = quat
        r1, r2, r3 = rod_params
        b1, b2, b3 = biases
        return OpNavAttitudeStateModel(
            time_retrieved=time,
            q1=q1,
            q2=q2,
            q3=q3,
            q4=q4,
            r1=r1,
            r2=r2,
            r3=r3,
            b1=b1,
            b2=b2,
            b3=b3,
            r1c1 = P[0,0], r1c2 = P[0,1], r1c3 = P[0,2], r1c4 = P[0,3], r1c5 = P[0,4], r1c6 = P[0,5],
            r2c1 = P[1,0], r2c2 = P[1,1], r2c3 = P[1,2], r2c4 = P[1,3], r2c5 = P[1,4], r2c6 = P[1,5],
            r3c1 = P[2,0], r3c2 = P[2,1], r3c3 = P[2,2], r3c4 = P[2,3], r3c5 = P[2,4], r3c6 = P[2,5],
            r4c1 = P[3,0], r4c2 = P[3,1], r4c3 = P[3,2], r4c4 = P[3,3], r4c5 = P[3,4], r4c6 = P[3,5],
            r5c1 = P[4,0], r5c2 = P[4,1], r5c3 = P[4,2], r5c4 = P[4,3], r5c5 = P[4,4], r5c6 = P[4,5],
            r6c1 = P[5,0], r6c2 = P[5,1], r6c3 = P[5,2], r6c4 = P[5,3], r6c5 = P[5,4], r6c6 = P[5,5],
        )

    def __repr__(self):
        return (
            f"<OpNavAttitudeStateModel(TimeRetrieved=({str(self.time_retrieved)}"
            f", quaternion=({self.q1}, {self.q2}, {self.q3}, {self.q4}), "
            f"rodriguez_params=({self.r1}, {self.r2}, {self.r3}), "
            f"baises=({self.b1}, {self.b2}, {self.b3}), "
            f"covariance matrix trace=({self.r1c1+self.r2c2+self.r3c3+self.r4c4+self.r5c5+self.r6c6}))>"
        )

class OpNavEphemerisModel(SQLAlchemyTableBase):
    __tablename__ = "opnav_ephemeris"

    id = Column(Integer, primary_key=True)
    time_retrieved = Column(DateTime)
    sun_x = Column(Float)
    sun_y = Column(Float)
    sun_z = Column(Float)
    sun_vx = Column(Float)
    sun_vy = Column(Float)
    sun_vz = Column(Float)
    moon_x = Column(Float)
    moon_y = Column(Float)
    moon_z = Column(Float)
    moon_vx = Column(Float)
    moon_vy = Column(Float)
    moon_vz = Column(Float)

    """
    Create an OpNavEphemerisModel instance
    @params
    [sun_eph]: sun ephemeris tuple in J2000 ECI: (x (km), y (km), z (km), vx (km/s), vy (km/s), vz (km/s))
    [moon_eph]: moon ephemeris tuple in J2000 ECI: (x (km), y (km), z (km), vx (km/s), vy (km/s), vz (km/s))
    [time]: mission time
    """
    @staticmethod
    def from_tuples(sun_eph, moon_eph, time):
        sx, sy, sz, svx, svy, svz = sun_eph
        mx, my, mz, mvx, mvy, mvz = moon_eph
        return OpNavEphemerisModel(
            time_retrieved=time,
            sun_x=sx,
            sun_y=sy,
            sun_z=sz,
            sun_vx=svx,
            sun_vy=svy,
            sun_vz=svz,
            moon_x=mx,
            moon_y=my,
            moon_z=mz,
            moon_vx=mvx,
            moon_vy=mvy,
            moon_vz=mvz,
        )

    def __repr__(self):
        return (
            f"<OpNavEphemerisModel(TimeRetrieved=({str(self.time_retrieved)}"
            f", sun ephemeris=({self.sun_x}, {self.sun_y}, {self.sun_z}, {self.sun_vx}, {self.sun_vy}, {self.sun_vz}) "
            f"moon ephemeris=({self.moon_x}, {self.moon_y}, {self.moon_z}, {self.moon_vx}, {self.moon_vy}, {self.moon_vz}))>"
        )

class OpNavCameraMeasurementModel(SQLAlchemyTableBase):
    __tablename__ = "opnav_camera_measurement_state"

    id = Column(Integer, primary_key=True)
    time_retrieved = Column(DateTime)
    ang_em = Column(Float)
    ang_es = Column(Float)
    ang_ms = Column(Float)
    e_dia = Column(Float)
    m_dia = Column(Float)
    s_dia = Column(Float)
    
    """
    Create an OpNavCameraMeasurementModel instance
    @params
    [measurement]: 6D camera measurement tuple representing angular separation and sizes (radians)
        Format:(z1 = angular separation between Earth & Moon, 
                z2 = angular separation between Earth & Sun,
                z3 = angular separation between Sun & Moon,
                z4 = angular Earth size, 
                z5 = angular Moon size, 
                z6 = angular Sun size)
    [time]: mission time of the measurements when trajectory quantities were calculated
    """
    @staticmethod
    def from_tuples(measurement:CameraMeasurementVector, time):
        z1 = measurement.get_angular_separation_earth_moon()
        z2 = measurement.get_angular_separation_earth_sun()
        z3 = measurement.get_angular_separation_moon_sun()
        z4 = measurement.get_angular_diameter_earth()
        z5 = measurement.get_angular_diameter_moon()
        z6 = measurement.get_angular_diameter_sun()
        return OpNavCameraMeasurementModel(
            time_retrieved=time,
            ang_em=z1,
            ang_es=z2,
            ang_ms=z3,
            e_dia=z4,
            m_dia=z5,
            s_dia=z6,
        )

    def __repr__(self):
        return (
            f"<OpNavCameraMeasurementModel(TimeRetrieved=({str(self.time_retrieved)}"
            f", camera measurement=({self.ang_em}, {self.ang_es}, {self.ang_ms}, {self.e_dia}, {self.m_dia}, {self.s_dia}))>"
        )

class OpNavGyroMeasurementModel(SQLAlchemyTableBase):
    __tablename__ = "opnav_gyro_measurement_state"

    id = Column(Integer, primary_key=True)
    time_retrieved = Column(DateTime)
    omegax = Column(Float)
    omegay = Column(Float)
    omegaz = Column(Float)

    """
    Create an OpNavGyroMeasurementModel instance
    @params
    [measurement]: 3D gyro measurement tuple representing angular velocity
        Format: (omegax, omegay, omegaz)
    [time]: mission time of the gyro reading
    """
    @staticmethod
    def from_tuples(measurement, time):
        omegax, omegay, omegaz = measurement
        return OpNavGyroMeasurementModel(
            time_retrieved=time,
            omegax=omegax,
            omegay=omegay,
            omegaz=omegaz
        )

    def __repr__(self):
        return (
            f"<OpNavGyroMeasurementModel(TimeRetrieved=({str(self.time_retrieved)}"
            f", gyro measurement=({self.omegax}, {self.omegay}, {self.omegaz}))>"
        )

class OpNavPropulsionModel(SQLAlchemyTableBase):
    __tablename__ = "opnav_propulsion_state"

    id = Column(Integer, primary_key=True)
    time_start = Column(DateTime)
    time_end = Column(DateTime)
    acceleration = Column(Float)

    """
    Create an OpNavPropulsionModel instance
    @params
    [acceleration]: acceleration magnitude caused by main thrust fire
    [time_start]: mission time of main thrust fire start
    [time_end]: mission time of main thrust fire end
    """
    @staticmethod
    def from_tuples(acceleration, time_start, time_end):
        return OpNavPropulsionModel(
            time_start=time_start,
            time_end=time_end,
            acceleration=acceleration,
        )

    def __repr__(self):
        return (
            f"<OpNavPropulsionModel(TimeStart=({str(self.time_start)}, {str(self.time_end)}"
            f", acceleration=({self.acceleration}))>"
        )

class RebootsModel(SQLAlchemyTableBase):
    __tablename__ = "Reboots"

    id = Column(Integer, primary_key=True)
    is_bootup = Column(Boolean)
    reboot_at = Column(DateTime)

    def __repr__(self):
        return f"<RebootsModel(is boot up?={self.is_bootup}, reboot_at={str(self.reboot_at)})>"


class GyroModel(SQLAlchemyTableBase):
    __tablename__ = "9DoF"

    id = Column(Integer, primary_key=True)
    time_polled = Column(Float)
    gyr_x = Column(Float)
    gyr_y = Column(Float)
    gyr_z = Column(Float)
    acc_x = Column(Float)
    acc_y = Column(Float)
    acc_z = Column(Float)
    mag_x = Column(Float)
    mag_y = Column(Float)
    mag_z = Column(Float)
    temperature = Column(Float)

    @staticmethod
    def from_tuple(gyro_tuple: tuple):
        gyro_data, acc_data, mag_data, temperature, time = gyro_tuple
        gx, gy, gz = gyro_data
        ax, ay, az = acc_data
        bx, by, bz = mag_data
        return GyroModel(
            time_polled=time,
            gyr_x=gx,
            gyr_y=gy,
            gyr_z=gz,
            acc_x=ax,
            acc_y=ay,
            acc_z=az,
            mag_x=bx,
            mag_y=by,
            mag_z=bz,
            temperature=temperature
        )

    def __repr__(self):
        return (
            f"<GyroModel("
            f"gyr=({self.gyr_x}, {self.gyr_y}, {self.gyr_z}),"
            f"acc=({self.acc_x}, {self.acc_y}, {self.acc_z}), "
            f"mag=({self.mag_x}, {self.mag_y}, {self.mag_z}),"
            f"temp={self.temperature}"
            f"time={self.time_polled})>"
        )


class RPiModel(SQLAlchemyTableBase):
    __tablename__ = "RPi"

    id = Column(Integer, primary_key=True)
    time_polled = Column(DateTime)
    cpu = Column(Integer)
    ram = Column(Integer)
    dsk = Column(Integer)
    tmp = Column(Integer)
    boot = Column(Float)
    uptime = Column(Float)

    @staticmethod
    def from_tuple(rpi_tuple: tuple):
        cpu, ram, dsk, boot_time, uptime, temp, poll_time = rpi_tuple
        temp = int(temp * 10)
        # we save 2 bytes of downlink by converting the rpi temperature to an int (which is then packed as a short
        # during transmission), but we don't lose any accuracy. On the GS we will need to divide the temperature by 10

        return RPiModel(
            time_polled=poll_time,
            cpu=cpu,
            ram=ram,
            dsk=dsk,
            boot=boot_time,
            uptime=uptime,
            tmp=temp
        )

    def __repr__(self):
        return (
            f"<RPiModel("
            f"cpu={self.cpu}, "
            f"ram={self.ram}, "
            f"dsk={self.dsk}, "
            f"temp={self.tmp}, "
            f"boot time={self.boot_time}, "
            f"uptime={self.uptime}, "
            f"poll time={self.time_polled})>"
        )


class GomModel(SQLAlchemyTableBase):
    __tablename__ = "Gom"
    # See drivers/power/power_structs.py line #115 for reference
    id = Column(Integer, primary_key=True)
    time_polled = Column(DateTime)
    vboost1 = Column(Integer)
    vboost2 = Column(Integer)
    vboost3 = Column(Integer)
    vbatt = Column(Integer)
    curin1 = Column(Integer)
    curin2 = Column(Integer)
    curin3 = Column(Integer)
    cursun = Column(Integer)
    cursys = Column(Integer)
    reserved1 = Column(Integer)
    curout1 = Column(Integer)
    curout2 = Column(Integer)
    curout3 = Column(Integer)
    curout4 = Column(Integer)
    curout5 = Column(Integer)
    curout6 = Column(Integer)
    outputs = Column(Integer)
    latchup1 = Column(Integer)
    latchup2 = Column(Integer)
    latchup3 = Column(Integer)
    latchup4 = Column(Integer)
    latchup5 = Column(Integer)
    latchup6 = Column(Integer)
    wdt_i2c_time_left = Column(Integer)
    wdt_gnd_time_left = Column(Integer)
    counter_wdt_i2c = Column(Integer)
    counter_wdt_gnd = Column(Integer)
    counter_boot = Column(Integer)
    bootcause = Column(Integer)
    battmode = Column(Integer)
    temp1 = Column(Integer)
    temp2 = Column(Integer)
    temp3 = Column(Integer)
    temp4 = Column(Integer)
    pptmode = Column(Integer)
    reserved2 = Column(Integer)

    @staticmethod
    def from_struct(eps_hk: eps_hk_t, poll_time):
        return GomModel(
            time_polled=poll_time,
            vboost1=eps_hk.vboost[0],
            vboost2=eps_hk.vboost[1],
            vboost3=eps_hk.vboost[2],
            vbatt=eps_hk.vbatt,
            curin1=eps_hk.curin[0],
            curin2=eps_hk.curin[1],
            curin3=eps_hk.curin[2],
            cursun=eps_hk.cursun,
            cursys=eps_hk.cursys,
            reserved1=eps_hk.reserved1,
            curout1=eps_hk.curout[0],
            curout2=eps_hk.curout[1],
            curout3=eps_hk.curout[2],
            curout4=eps_hk.curout[3],
            curout5=eps_hk.curout[4],
            curout6=eps_hk.curout[5],
            outputs=int(str(eps_hk.output).replace(',', '').replace(' ', '')[1:-1], 2),
            latchup1=eps_hk.latchup[0],
            latchup2=eps_hk.latchup[1],
            latchup3=eps_hk.latchup[2],
            latchup4=eps_hk.latchup[3],
            latchup5=eps_hk.latchup[4],
            latchup6=eps_hk.latchup[5],
            wdt_i2c_time_left=eps_hk.wdt_i2c_time_left,
            wdt_gnd_time_left=eps_hk.wdt_gnd_time_left,
            counter_wdt_i2c=eps_hk.counter_wdt_i2c,
            counter_wdt_gnd=eps_hk.counter_wdt_gnd,
            counter_boot=eps_hk.counter_boot,
            temp1=eps_hk.temp[0],
            temp2=eps_hk.temp[1],
            temp3=eps_hk.temp[2],
            temp4=eps_hk.temp[3],
            bootcause=eps_hk.bootcause,
            battmode=eps_hk.battmode,
            pptmode=eps_hk.pptmode,
            reserved2=eps_hk.reserved2
        )

    def __repr__(self):
        return (f""
                f""
                f""
                f"")
        # TODO


class TelemetryModel(SQLAlchemyTableBase):
    __tablename__ = "Telemetry"

    id = Column(Integer, primary_key=True)
    time_polled = Column(DateTime)

    # GOM DATA
    GOM_vboost1 = Column(Integer)
    GOM_vboost2 = Column(Integer)
    GOM_vboost3 = Column(Integer)
    GOM_vbatt = Column(Integer)
    GOM_curin1 = Column(Integer)
    GOM_curin2 = Column(Integer)
    GOM_curin3 = Column(Integer)
    GOM_cursun = Column(Integer)
    GOM_cursys = Column(Integer)
    GOM_reserved1 = Column(Integer)
    GOM_curout1 = Column(Integer)
    GOM_curout2 = Column(Integer)
    GOM_curout3 = Column(Integer)
    GOM_curout4 = Column(Integer)
    GOM_curout5 = Column(Integer)
    GOM_curout6 = Column(Integer)
    GOM_outputs = Column(Integer)
    GOM_latchup1 = Column(Integer)
    GOM_latchup2 = Column(Integer)
    GOM_latchup3 = Column(Integer)
    GOM_latchup4 = Column(Integer)
    GOM_latchup5 = Column(Integer)
    GOM_latchup6 = Column(Integer)
    GOM_wdt_i2c_time_left = Column(Integer)
    GOM_wdt_gnd_time_left = Column(Integer)
    GOM_counter_wdt_i2c = Column(Integer)
    GOM_counter_wdt_gnd = Column(Integer)
    GOM_counter_boot = Column(Integer)
    GOM_bootcause = Column(Integer)
    GOM_battmode = Column(Integer)
    GOM_temp1 = Column(Integer)
    GOM_temp2 = Column(Integer)
    GOM_temp3 = Column(Integer)
    GOM_temp4 = Column(Integer)
    GOM_pptmode = Column(Integer)
    GOM_reserved2 = Column(Integer)

    # RTC DATA
    RTC_measurement_taken = Column(DateTime)

    # RPi DATA
    RPI_cpu = Column(Integer)
    RPI_ram = Column(Integer)
    RPI_dsk = Column(Integer)
    RPI_tmp = Column(Integer)
    RPI_boot = Column(Float)
    RPI_uptime = Column(Float)

    # GYRO DATA
    GYRO_gyr_x = Column(Float)
    GYRO_gyr_y = Column(Float)
    GYRO_gyr_z = Column(Float)
    GYRO_acc_x = Column(Float)
    GYRO_acc_y = Column(Float)
    GYRO_acc_z = Column(Float)
    GYRO_mag_x = Column(Float)
    GYRO_mag_y = Column(Float)
    GYRO_mag_z = Column(Float)
    GYRO_temperature = Column(Float)

    # THERMOCOUPLE DATA
    THERMOCOUPLE_pressure = Column(Float)

    # PRESSURE DATA
    PRESSURE_pressure = Column(Float)


def create_sensor_tables(engine):
    SQLAlchemyTableBase.metadata.create_all(engine)
    create_session.configure(bind=engine)
    return create_session

def create_sensor_tables_from_path(path: str):
    engine = create_engine(path)
    return create_sensor_tables(engine)
