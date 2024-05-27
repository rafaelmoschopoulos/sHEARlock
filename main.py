from shearlock import Shearlock
from utils import get_args


if __name__ == '__main__':
    app_instance = Shearlock(*get_args(default_buffer_length=3.0, default_buffer_update_period=0.2,
                                       default_device_name='BlackHole'))
    app_instance.run()
