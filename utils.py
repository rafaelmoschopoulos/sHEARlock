import argparse
import sounddevice as sd


def get_error_msg(e: Exception) -> str:
    return type(e).__name__ + ": " + str(e)


def get_args(default_buffer_length: float, default_buffer_update_period: float, default_device_name: str)\
        -> tuple[int, float, float]:
    def int_or_str(text):
        try:
            return int(text)
        except ValueError:
            return text

    def get_blackhole_input_id():
        input_dev_found = -1
        for i, dic in enumerate(sd.query_devices()):
            if default_device_name in dic['name']:
                input_dev_found = i
        return input_dev_found

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-id', '--input-device', type=int_or_str,
                        help='input device ID or substring', nargs='?', default=get_blackhole_input_id())
    parser.add_argument('-bl', '--buffer-length', type=float, help='buffer length', nargs='?',
                        default=default_buffer_length)
    parser.add_argument('-bup', '--buffer-update-period', type=float, help='buffer update period',
                        nargs='?', default=default_buffer_update_period)
    parser.add_argument('-pdev', '--print-device-id', action='store_true')
    try:
        args = parser.parse_args()

        if args.print_device_id:
            print(sd.query_devices())

        if args.input_device >= len(sd.query_devices()):
            raise RuntimeError("Input device index out of range.")
        if args.input_device == -1:
            raise RuntimeError('BlackHole driver not found, and no other valid input device specified.')
        return args.input_device, args.buffer_length, args.buffer_update_period
    except Exception as e:
        parser.exit(status=1, message=get_error_msg(e))