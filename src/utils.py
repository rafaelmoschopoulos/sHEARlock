import argparse
import sounddevice as sd


def get_error_msg(e: Exception) -> str:
    return type(e).__name__ + ": " + str(e)


def get_args(device_name, buffer_length, buffer_update_period, chunk_length, chunk_count, pred_threshold):
    def int_or_str(text):
        try:
            return int(text)
        except ValueError:
            return text

    def get_input_id_from_name(dev_name):
        input_dev_id_found = -1
        for i, dic in enumerate(sd.query_devices()):
            if dev_name in dic['name']:
                input_dev_id_found = i
        return input_dev_id_found

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-id', '--input-device', type=int_or_str,
                        help='input device ID or substring', nargs='?', default=get_input_id_from_name(device_name))
    parser.add_argument('-bl', '--buffer-length', type=float, help='buffer length', nargs='?',
                        default=buffer_length)
    parser.add_argument('-bup', '--buffer-update-period', type=float, help='buffer update period',
                        nargs='?', default=buffer_update_period)
    parser.add_argument('-cl', '--chunk-length', type=float, help='chunk length',
                        nargs='?', default=chunk_length)
    parser.add_argument('-cc', '--chunk-count', type=int, help='chunk count',
                        nargs='?', default=chunk_count)
    parser.add_argument('-pt', '--prediction-threshold', type=float, help='prediction threshold',
                        nargs='?', default=pred_threshold)
    parser.add_argument('-pdev', '--print-device-id', action='store_true')

    try:
        args = parser.parse_args()

        if args.print_device_id:
            print(sd.query_devices())

        dev_id = get_input_id_from_name(args.input_device) if isinstance(args.input_device, str) else args.input_device

        if dev_id >= len(sd.query_devices()):
            raise RuntimeError("Input device index out of range.")
        if args.input_device == -1:
            raise RuntimeError('BlackHole driver not found, and no other valid input device specified.')
        return (dev_id, args.buffer_length, args.buffer_update_period, args.chunk_length, args.chunk_count,
                args.prediction_threshold)
    except Exception as e:
        parser.exit(status=1, message=get_error_msg(e))
