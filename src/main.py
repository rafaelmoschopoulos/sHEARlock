from shearlock import Shearlock
from utils import get_args


if __name__ == '__main__':
    defaults = {
        'buffer_length': 5,
        'buffer_update_period': 0.5,
        'device_name': 'BlackHole',
        'model_path': '../train/model.pkl',
        'chunk_length': 1.0,
        'pred_threshold': 0.9,
        'chunk_count': 20
    }

    app_instance = Shearlock(*get_args(**defaults))
    app_instance.run()
