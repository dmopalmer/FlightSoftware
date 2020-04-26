import gc
from time import sleep
import os

from utils.constants import (  # noqa F401
    LOW_CRACKING_PRESSURE,
    EXIT_LOW_BATTERY_MODE_THRESHOLD,
    HIGH_CRACKING_PRESSURE,
    IDEAL_CRACKING_PRESSURE,
    BOOTUP_SEPARATION_DELAY,
    FMEnum,
)
from utils.exceptions import UnknownFlightModeException

# Necessary modes to implement
# BootUp, Restart, Normal, Eclipse, Safety, Electrolysis, Propulsion,
# Attitude Adjustment, Transmitting, OpNav (image processing)
# TestModes

no_transition_modes = [
    FMEnum.SensorMode.value,
    FMEnum.TestMode.value,
    FMEnum.CommsMode.value,
]


class FlightMode:
    def __init__(self, parent):
        self.parent = parent
        self.task_completed = False

    def update_state(self):
        flight_mode_id = self.flight_mode_id
        if flight_mode_id == FMEnum.LowBatterySafety.value:
            if (
                self.gom.read_battery_percentage() >= EXIT_LOW_BATTERY_MODE_THRESHOLD  # noqa E501
            ):
                self.parent.replace_flight_mode_by_id(FMEnum.Normal.value)

        elif flight_mode_id == FMEnum.Safety.value:
            raise NotImplementedError  # TODO

        elif flight_mode_id == FMEnum.Normal.value:
            pass
            # TODO do I need to enter electrolysis to prepare for maneuver?
            # do I need to start a maneuver?
            # do I need to run OpNav?

        elif flight_mode_id == FMEnum.Boot.value:
            pass

        elif flight_mode_id == FMEnum.Electrolysis.value:
            if self.task_completed is True:
                self.parent.replace_flight_mode_by_id(FMEnum.Maneuver.value)

        elif flight_mode_id == FMEnum.Restart.value:
            if self.task_completed is True:
                self.parent.replace_flight_mode_by_id(FMEnum.Normal.value)

        elif flight_mode_id == FMEnum.Maneuver.value:
            if self.task_completed is True:
                self.parent.replace_flight_mode_by_id(FMEnum.Normal.value)

        elif flight_mode_id == FMEnum.OpNav.value:
            if self.task_completed is True:
                self.parent.replace_flight_mode_by_id(FMEnum.Normal.value)

        elif flight_mode_id in no_transition_modes:
            pass

        else:
            raise UnknownFlightModeException(flight_mode_id)

    def run_mode(self):
        pass

    def execute_commands(self):
        if len(self.parent.commands_to_execute) == 0:
            pass  # TODO
        # If I have no commands to execute do nothing

    def read_sensors(self):
        pass

    def completed_task(self):
        self.task_completed = True

    # Autonomous actions to maintain safety
    def automatic_actions(self):
        pass

    def write_telemetry(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        pass


class TestMode(FlightMode):

    flight_mode_id = FMEnum.TestMode.value

    def __init__(self, parent):
        super().__init__(parent)
        raise NotImplementedError


class CommsMode(FlightMode):

    flight_mode_id = FMEnum.CommsMode.value

    def __init__(self, parent):
        super().__init__(parent)
        raise NotImplementedError


class SensorMode(FlightMode):

    flight_mode_id = FMEnum.SensorMode.value

    def __init__(self, parent):
        super().__init__(parent)
        raise NotImplementedError


# BootUp mode tasks:
# Sleep for 30 seconds to reach safe distance from Artemis I
class BootUpMode(FlightMode):

    flight_mode_id = FMEnum.Boot.value

    def __init__(self, parent):
        super().__init__(parent)
        self.set_started_bootup()
        print("Booting up...")

    def set_started_bootup(self):
        # TODO implement logger to actually put logs in this directory
        os.makedirs(self.parent.log_dir)

    # Sleep for a delay set by BOOTUP_SEPARATION_DELAY if I haven't
    # If I've already completed the delay, do nothing
    # Await separation command from ground station
    def run_mode(self):
        if not self.delay_completed:
            sleep(BOOTUP_SEPARATION_DELAY)
            self.task_completed()


class RestartMode(FlightMode):

    flight_mode_id = FMEnum.Restart.value

    def __init__(self, parent):
        super().__init__(parent)
        self.clear_unnecessary_storage_and_memory()
        self.check_sensors()
        self.completed_task()
        # TODO
        # trigger restart again if necessary
        # make note of turning back on and immediately
        # # downlink restart information
        # increment counter for consecutive restarts in db

    def clear_unnecessary_storage_and_memory(self):
        gc.collect()
        # TODO clean up storage if necessary
        # pseudocode, if OS = raspian and environment = flight, not test:
        #   clean up storage and memory

    # TODO ensure sensors are working correctly
    def check_sensors(self):
        pass

    # Restart is handled in initialization
    # Therefore, should get updated to Normal before
    # ever running
    def run_mode(self):
        pass


# Electrolyze until pressure in the tank reaches IDEAL_CRACKING_PRESSURE
# TODO determine correct values based on testing
# TODO determine which of cracking pressures to change on
# NOTE: if we go with LOW_CRACKING_PRESSURE ensure that pressure
# doesn't dip below in interval between exiting
# electrolysis and hitting ignition
class ElectrolysisMode(FlightMode):

    flight_mode_id = FMEnum.Electrolysis.value

    def __init__(self, parent):
        super().__init__(parent)
        self.pressure_sensor = parent.pressure_sensor
        self.gom = parent.gom

    # Turn electrolysis on if propellant tank is below IDEAL_CRACKING_PRESSURE
    # If we have reached this cracking pressure, then turn electrolysis off
    # and set task_completed to True
    def run_mode(self):
        # If electrolyzing is turned on, check to see if I should turn it off
        curr_pressure = self.pressure_sensor.read_value()
        if curr_pressure >= IDEAL_CRACKING_PRESSURE:
            self.gom.set_electrolysis(False)
            self.completed_task()
        else:
            self.gom.set_electrolysis(True)


class LowBatterySafetyMode(FlightMode):

    flight_mode_id = FMEnum.LowBatterySafety.value

    def __init__(self, parent):
        super().__init__(parent)

    # TODO point solar panels directly at the sun
    # check power supply to see if I can transition back to NormalMode
    def run_mode(self):
        pass


# Model for FlightModes that require precise timing
# Pause garbage collection and anything else that could
# interrupt critical thread
class PauseBackgroundMode(FlightMode):
    def __init__(self, parent):
        super().__init__(parent)

    def __enter__(self):
        gc.disable()

    def __exit__(self, exc_type, exc_val, exc_tb):
        gc.collect()
        gc.enable()


class ManeuverMode(PauseBackgroundMode):
    flight_mode_id = FMEnum.Maneuver.value

    def __init__(self, parent):
        super().__init__(parent)
        self.goal = 10
        self.moves_towards_goal = 0

    def set_goal(self, goal: int):
        self.goal = 10

    def execute_maneuver_towards_goal(self):
        self.moves_towards_goal += 1

    # TODO implement actual maneuver execution
    # check if exit condition has completed
    def run_mode(self):
        self.moves_towards_goal()
        if self.moves_towards_goal >= self.goal:
            self.task_completed()


class SafeMode(FlightMode):

    flight_mode_id = FMEnum.Safety.value

    def __init__(self, parent):
        super().__init__(parent)

    def run_mode(self):
        print("Execute safe mode")


class NormalMode(FlightMode):

    flight_mode_id = FMEnum.Normal.value

    def __init__(self, parent):
        super().__init__(parent)

    def run_mode(self):
        print("Execute normal mode")
