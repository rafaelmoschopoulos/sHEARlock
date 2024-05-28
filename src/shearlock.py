import rumps
from src.predictor import Predictor
from utils import get_error_msg
from listener import Listener
import numpy as np
import queue

class Shearlock(rumps.App):
    def __init__(self, input_device, model_path: str, buffer_length, buffer_update_period, chunk_length: float,
                 chunk_cnt: int, pred_threshold: float):
        super(Shearlock, self).__init__("sHEARlock", quit_button=None)

        self._icon_path = "../img/icon.png"
        self.icon = self._icon_path
        self.menu.add(rumps.MenuItem("Start", callback=self._start_monitoring))
        self.menu.add(rumps.MenuItem("Stop", callback=self._stop_monitoring))
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Terminate", callback=self._quit_app))
        self.label = rumps.MenuItem(title="0% deepfake")

        self._detection_queue = queue.Queue()
        self._exception_queue = queue.Queue()
        self.timer_detection = rumps.Timer(self._process_detection_queue, buffer_update_period)
        self.timer_exception = rumps.Timer(self._process_exception_queue, buffer_update_period)

        self.timer_exception.start()

        self._listener_args = {
            'input_device': input_device,
            'buffer_length': buffer_length,
            'buffer_update_period': buffer_update_period,
            'exception_queue': self._exception_queue,
            'callback_queue': self._detection_queue
        }
        self._listener = Listener(**self._listener_args)

        self._predictor = Predictor(model_path, buffer_length,
                                    chunk_length, self._listener.get_sample_rate(), chunk_cnt,
                                    pred_threshold)

    def _detect(self, buffer: np.array):
        result = self._predictor.fake_ratio(buffer)
        print(result)

        self.label.title = str(int(result * 100)) + "% deepfake"
        """
        if self._predictor.is_deepfake(buffer):
            print("Deepfake detected")
        else:
            print("No deepfake")
        """
    def _process_detection_queue(self, _):
        while not self._detection_queue.empty():
            result = self._predictor.fake_ratio(self._detection_queue.get())
            self.label.title = str(int(result * 100)) + "% deepfake"

    def _process_exception_queue(self, _):
        while not self._exception_queue.empty():
            self._handle_unrecoverable_error(self._exception_queue.get())

    def _start_monitoring(self, _):
        if self._listener.is_alive():
            return
        if rumps.alert(title="Monitoring initiation", message="sHEARlock will begin monitoring.", ok="OK",
                       cancel="Cancel", icon_path=self._icon_path) == 0:
            return
        self.menu.insert_before("Start", self.label)
        self._listener = Listener(**self._listener_args)
        self._listener.start_monitoring()
        self.timer_detection.start()

    def _stop_monitoring(self, _):
        if not self._listener.is_alive():
            return
        if rumps.alert(title="Monitoring session in progress", message="Do you want to terminate this session?", ok="Yes",
                       cancel="No", icon_path=self._icon_path) == 0:
            return
        del self.menu["0% deepfake"]
        self.timer_detection.stop()
        self._listener.stop_monitoring()

    def _quit_app(self, _):
        if self._listener.is_alive():
            self._listener.stop_monitoring()
        rumps.quit_application()

    def _handle_unrecoverable_error(self, e: Exception):
        rumps.alert(title="Unexpected error occurred", message=get_error_msg(e), ok="Abort")
        print(get_error_msg(e))
        self._quit_app(None)
