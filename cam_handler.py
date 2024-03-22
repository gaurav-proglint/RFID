from threading import Thread
import time
import cv2
import platform
import threading
import queue

global_data = {
   "cam_url":["rtsp://admin:Proglint321@192.168.1.230:554/cam/realmonitor?channel=1&subtype=0",
              "rtsp://admin:Proglint321@192.168.1.221:554/cam/realmonitor?channel=1&subtype=0",
              "rtsp://admin:Proglint321@192.168.1.220:554/cam/realmonitor?channel=1&subtype=0",
              "rtsp://admin:Proglint321@192.168.1.233:554/cam/realmonitor?channel=1&subtype=0"]
}


class Camera_handler(object):
    def __init__(self):
        self.cam_handles = {}
        self.capture_status = {}
        self.thread = {}

        self.camera_ids = global_data.get('cam_url')

        for index, cam_id in enumerate(self.camera_ids, 1):
            cam = self.connect_camera(cam_id)
            frame_queue = queue.Queue()
            start_event = threading.Event()
            t = Thread(target=self._reader, args=([cam_id, cam, frame_queue, start_event]))
            self.thread[cam_id] = {
                'frame_queue': frame_queue,
                'start_event': start_event,
                't': t
            }
            t.daemon = True
            t.start()
            

    def _reader(self, id, cam, frame_queue, start_event):
        try:
            wait_count = 0
            while True:
                cam.grab()
                wait_count = 0
                if start_event.is_set():
                    ret, frame = cam.read()
                    if not ret:
                        wait_count += 1
                        if wait_count == 10:
                            print(f'Reconnecting camera {id}')
                            time.sleep(2)
                            cam = self.connect_camera(id)
                    else:
                        frame_queue.put(frame)
                        start_event.clear()
                time.sleep(0.01)
        except Exception as e:
            print('Print error', e)
    def connect_camera(self, cam_id):
        print(f'Connecting {cam_id}')
        cam_url = cam_id
        if cam_id.isnumeric():
            cam_url = int(cam_id)
        if self.cam_handles.get(cam_id):
            try:
                self.cam_handles.get(cam_id).release()
            except:
                print(f'Exception on release cam {cam_id}')
        if "macOS" in platform.platform():
            cam_handle = cv2.VideoCapture(cam_url)
        elif "Windows" in platform.platform():
            cam_handle = cv2.VideoCapture(cam_url)
        else:
            cam_handle = cv2.VideoCapture(cam_url)
        if cam_handle.isOpened():
            self.cam_handles[(cam_id)] = cam_handle
            self.capture_status[(cam_id)] = True
        else:
            self.capture_status[(cam_id)] = False
        # cam_handle.release()
        return cam_handle

    def release(self):
        [cam.release() for _, cam in self.cam_handles.items()]
    
    def get_status(self):
        return self.capture_status

    def read_frame(self, cam_id):
        start = time.perf_counter()
        print(f'process called for camera {cam_id}')
        thread = self.thread.get((cam_id))
        skip_count = 30
        cnt = 0
        detect_count = 4
        try:
            frame_list = []
            while True:
                thread.get('start_event').set()
                while True:
                    try:
                        frame = thread.get('frame_queue').get()
                    except queue.Empty:
                        continue
                    break
                return True, frame, frame_list
        except Exception as e:
            print(f'Exception for {cam_id} : {e}')
            return None, False, []
    def check_status(self, cam_id):
        try:
            cam_handle = self.cam_handles.get(cam_id)
            return cam_handle.isOpened()
        except Exception as e:
            return False

# camera_handler = Camera_handler()
