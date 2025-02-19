from pytest import raises

from communications.commands import CommandHandler
from utils.struct import unpack_double, pack_double
from utils.exceptions import SerializationException
from utils.constants import MAC


class TestCommandHandler:
    def test_packers_unpackers_match(self):
        ch = CommandHandler()

        assert set(ch.packers.keys()) == set(ch.unpackers.keys())

    def test_register_new_codec(self):
        arg = "testarg"
        ch = CommandHandler()
        ch.register_new_codec(arg, pack_double, unpack_double)
        assert arg in ch.unpackers and arg in ch.packers

        with raises(SerializationException):
            ch.register_new_codec(arg, pack_double, unpack_double)

    def test_command_serialization(self):
        # Both are doubles
        arg1 = "arg1"
        arg2 = "arg2"
        ch = CommandHandler()
        print(f"Packers: {ch.packers}")
        command_args = [arg1, arg2]
        command_data_tuple = (command_args, 16)
        application_id = 78
        command_dict = {application_id: command_data_tuple}
        mode_id = 255

        kwargs = {
            arg1: 78.1,
            arg2: 99.5,
        }
        command_counter = 1
        ch.register_new_command(mode_id, application_id, **kwargs)
        command_buffer = ch.pack_command(command_counter, mode_id, application_id, **kwargs)

        assert len(command_buffer) == ch.get_command_size(mode_id, application_id)

        unpacked_mac, unpacked_counter, unpacked_mode, unpacked_app, unpacked_args = ch.unpack_command(command_buffer)

        print(unpacked_args)
        assert unpacked_mode == mode_id
        assert unpacked_app == application_id
        assert unpacked_args[arg1] == kwargs[arg1]
        assert unpacked_args[arg2] == kwargs[arg2]
        assert unpacked_counter == command_counter
        assert unpacked_mac == MAC


tch = TestCommandHandler()
tch.test_packers_unpackers_match()
tch.test_register_new_codec()
# tch.test_command_serialization()
