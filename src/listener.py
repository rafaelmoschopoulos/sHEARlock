import sounddevice as sd
import threading
import numpy as np


class Listener(threading.Thread):
    def __init__(self, input_device: int, buffer_length: float, buffer_update_period: float,
                 exception_queue, callback_queue):
        super().__init__()

        self._input_device = input_device
        self._input_channels = sd.query_devices(self._input_device)['max_input_channels']
        self._sample_rate = sd.query_devices(self._input_device)['default_samplerate']

        self._buffer_size = int(buffer_length * self._sample_rate)
        self._buffer_update_block_size = int(buffer_update_period * self._sample_rate)
        self._buffer = np.zeros(self._buffer_size, dtype=np.float32)

        self._stream = None
        self._stream_stop_event = threading.Event()

        self._callback_queue = callback_queue
        self._exception_queue = exception_queue

    def start_monitoring(self):
        self.start()

    def is_monitoring(self):
        return not self._stream_stop_event.is_set()

    def get_sample_rate(self):
        return self._sample_rate

    def stop_monitoring(self):
        self._stream_stop_event.set()
        if self._stream:
            self._stream.close()
        self.join()

    def _update_buffer(self, indata: np.ndarray, frames: int, time, status):
        try:
            if status:
                print(status)
            self._buffer = np.roll(self._buffer, -frames, axis=0)
            self._buffer[-frames:] = np.sum(indata, axis=1) / indata.shape[1]
            self._callback_queue.put(self._buffer)
        except Exception as e:
            self._exception_queue.put(e)

    def run(self):
        try:
            self._stream = sd.InputStream(device=self._input_device, samplerate=self._sample_rate,
                                          blocksize=self._buffer_update_block_size, channels=self._input_channels,
                                          callback=self._update_buffer)
            with self._stream:
                while not self._stream_stop_event.is_set():
                    sd.sleep(1000)
        except Exception as e:
            self._exception_queue.put(e)
