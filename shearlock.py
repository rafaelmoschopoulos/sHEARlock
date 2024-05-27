import rumps
import sounddevice as sd
import threading
import numpy as np
from utils import get_error_msg


class Shearlock(rumps.App):
    def __init__(self, input_device: int, buffer_length: float, buffer_update_period: float):
        super(Shearlock, self).__init__("sHEARlock", quit_button=None)
        self.menu.add(rumps.MenuItem("Start", callback=self._start_monitoring))
        self.menu.add(rumps.MenuItem("Stop", callback=self._stop_monitoring))
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Terminate", callback=self._quit_app))

        self.__input_device = input_device
        self.__input_channels = sd.query_devices(input_device)['max_input_channels']
        self.__sample_rate = sd.query_devices(input_device)['default_samplerate']

        self.__buffer_size = int(buffer_length * self.__sample_rate)
        self.__buffer_update_block_size = int(buffer_update_period * self.__sample_rate)
        self.__buffer = np.zeros(self.__buffer_size, dtype=np.float32)

        self.__stream = None
        self.__stream_thread = None
        self.__stream_stop_event = threading.Event()
        self.__stream_stop_event.set()

    def _start_monitoring(self, _):

        if not self.__stream_stop_event.is_set():
            return
        if rumps.alert(title="Monitoring initiation", message="sHEARlock will begin monitoring.", ok="OK",
                       cancel="Cancel") == 0:
            return
        self.__stream_stop_event.clear()
        self.__stream_thread = threading.Thread(target=self.__start_stream)
        self.__stream_thread.start()

    def _stop_monitoring(self, _):
        if self.__stream_stop_event.is_set():
            return
        if rumps.alert(title="Monitoring session in progress", message="Do you want to terminate this session?", ok="Yes",
                       cancel="No") == 0:
            return
        self.__stream.close()
        self.__stream_stop_event.set()
        self.__stream_thread.join()
        self.__stream = None

    def _quit_app(self, _):
        if self.__stream:
            self.__stream_stop_event.set()
            self.__stream.close()
            self.__stream_thread.join()
        rumps.quit_application()

    def __update_buffer(self, indata: np.ndarray, frames: int, time, status):
        try:
            if status:
                print(status)
            self.__buffer = np.roll(self.__buffer, -frames, axis=0)
            self.__buffer[-frames:] = np.sum(indata, axis=1) / indata.shape[1]
        except Exception as e:
            self.__handle_unrecoverable_error(e)

    def __start_stream(self):
        try:
            self.__stream = sd.InputStream(device=self.__input_device, samplerate=self.__sample_rate,
                                           blocksize=self.__buffer_update_block_size, channels=self.__input_channels,
                                           callback=self.__update_buffer)
            with self.__stream:
                while not self.__stream_stop_event.is_set():
                    sd.sleep(1000)
        except Exception as e:
            self.__handle_unrecoverable_error(e)

    def __handle_unrecoverable_error(self, e: Exception):
        rumps.alert(title="Unexpected error occurred", message=get_error_msg(e), ok="Abort")
        self._quit_app(None)
