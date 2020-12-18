from drivers.gom import Gomspace
from datetime import datetime
from utils.log import get_log
from drivers.gyro import GyroSensor
from time import sleep
import threading


# from utils.constants import BURNWIRE_DURATION


def gyro_thread():
    gyro_data = []
    logger.info("Reading Gyro data (rad/s)")
    for i in range(100):
        gyro_reading = gyro.get_gyro()
        gyro_time = datetime.now().time().isoformat()
        gyro_list = list(gyro_reading)
        gyro_list.append(gyro_time)
        gyro_data.append(gyro_list)
        sleep(0.05)

    # writes gyro data to gyro_data.txt. Caution, this file will be overwritten with every successive test
    logger.info("Writing gyro data to file")
    with open('gyro_data.txt', 'w') as filehandle:
        filehandle.writelines("%s\n" % line for line in gyro_data)


if __name__ == '__main__':
    logger = get_log()
    gyro = GyroSensor()
    gom_controller = Gomspace()

    # start new thread to log gyro data
    gyro_threader = threading.Thread(target=gyro_thread)
    gyro_threader.start()
    gom_controller.burnwire2(2)
