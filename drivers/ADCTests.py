# CislunarExplorers/FlightSoftware/drivers/ADCTests.py
#
# Created by Stefan Brechter (scb262@cornell.edu) on 03/11/2020
#
# Cislunar Explorers
# Space Systems Design Studio
# Cornell University
#
# For detailed descriptions and analysis of the following test file please
# look at the accompanying End of Semester Report found here:
# https://cornell.app.box.com/file/664230352636

from ADCDriver import ADC
import time
from utils.log import get_log

test_log = get_log()

assert sum([1, 2, 3]) == 6, "Should be 6"


def test_ADC_initialize():
    return ADC()


def test_ADC_read_pressure(testADC):
    test_log.info(testADC.read_pressure())


def test_ADC_read_pressure_continuous(testADC):
    while True:
        test_log.info(testADC.read_pressure())
        time.sleep(1)


def test_ADC_read_pressure_20(testADC):
    x = 0
    test_log.info(
        "These are pressure readings when the analog to digital converter is connected to the 0 volt ground pin, 3.3V, and 5V on the RPi.")
    test_log.info("Ouput given in psi.")
    test_log.info("Readings taken once per second for 20 seconds.")
    while x < 20:
        test_ADC_read_pressure(testADC)
        x = x + 1
        time.sleep(1)


def test_ADC_read_temperature(testADC):
    test_log.info("--------------------------")
    cel = testADC.read_temperature()

    test_log.info(f"{cel} degC; {cel * 1.8 + 32} degF ")


def test_ADC_read_temperature_continuous(testADC):
    while True:
        test_ADC_read_temperature(testADC)
        time.sleep(1)


def test_ADC_read_temperature_20(testADC):
    x = 0
    while x < 20:
        test_ADC_read_temperature(testADC)
        x = x + 1
        time.sleep(1)


def test_ADC_get_gyro_temp(testADC):
    test_log.info("Cold junction temperature fro gyro sensor in Celsius:")
    test_log.info(testADC.get_gyro_temp())


if True:
    testADC = test_ADC_initialize()
    test_ADC_get_gyro_temp(testADC)
    # test_ADC_read_pressure_20(testADC)
    print("Conversion sanity check: 25.6 degrees")
    print(testADC.convert_volt_to_temp(testADC, testADC.convert_temp_to_volt(25.6)))
    print("Conversion sanity check: 2.023 mV")
    print(testADC.convert_temp_to_volt(testADC, testADC.convert_volt_to_temp(2.023)))
    test_ADC_read_temperature_continuous(testADC)
