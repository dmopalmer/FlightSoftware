#!/usr/bin/python
#
# CislunarExplorers/FlightSoftware/drivers/ADCDriver.py
#
# Created by Stefan Brechter (scb262@cornell.edu) on 03/11/2020
#
# Cislunar Explorers
# Space Systems Design Studio
# Cornell University
#
# For detailed descriptions and analysis of the following driver please
# look at the accompanying End of Semester Report found here:
# https://cornell.app.box.com/file/664230352636

import ADS1115
from drivers.gyro import GyroSensor


class ADC:
    """Analog to digital converter"""
    # Polynomial approximation constants for the thermocouple conversion from voltage to temperature.
    T0 = -8.7935962e0

    V0 = -3.4489914e-1

    P1 = 2.5678719e1
    P2 = -4.9887904e-1
    P3 = -4.4705222e-1
    P4 = -4.4869203e-2

    Q1 = 2.3893439e-4
    Q2 = -2.0397750e-2
    Q3 = -1.8424107e-3

    # Polynomial approximation constants for the thermocouple conversion from temperature to voltage.
    T0T = 2.5e01

    V0T = 1.0003453e0

    P1T = 4.0514854e-2
    P2T = -3.8789638e-5
    P3T = -2.8608478e-6
    P4T = -9.5367041e-10

    Q1T = -1.3948675e-3
    Q2T = -6.7976627e-5

    def __init__(self, gyro: GyroSensor):
        self.ads = ADS1115.ADS1115()
        self.gyro = gyro

    # Read the fuel tank pressure from the pressure transducer at channel 0 on the ADS1115
    def read_pressure(self):  # psi
        milVolts = self.ads.readADCSingleEnded(channel=0, pga=6144, sps=64)
        pressure = round(milVolts / 5000 * 300, 3)
        return pressure

    # Read the fuel tank temperature from thermocouple at channels 2 and 3 on the ADS1115
    # Requires a cold junction temperature taken from the Adafruit BNO055 gyroscopic sensor
    def read_temperature(self):
        hot_junc_volt = self.ads.readADCSingleEnded(channel=1, pga=256, sps=64)
        cold_junc_temp = self.get_gyro_temp()
        # Need cold junction voltage converted from temperature
        cold_junc_volt = self.convert_temp_to_volt(cold_junc_temp)
        # Add the hot and cold junction voltages and convert to temperature
        temperature = self.convert_volt_to_temp(hot_junc_volt + cold_junc_volt)

        return temperature

    def get_gyro_temp(self):
        return self.gyro.get_temp()

    def convert_temp_to_volt(self, temp):
        dif = temp - self.T0T

        num = dif * (self.P1T + dif * (self.P2T + dif * (self.P3T + self.P4T * dif)))
        denom = 1 + dif * (self.Q1T + self.Q2T * dif)

        voltage = self.V0T + num / denom

        return voltage

    def convert_volt_to_temp(self, voltage):
        dif = voltage - self.V0

        num = (dif) * (self.P1 + dif * (self.P2 + dif * (self.P3 + dif * self.P4)))
        denom = 1 + dif * (self.Q1 + dif * (self.Q2 + self.Q3 * dif))

        temperature = self.T0 + num / denom

        return temperature
