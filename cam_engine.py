import cv2
import time
import threading
import numpy as np
import pyvirtualcam
from typing import Callable, Optional

class VirtualCamEngine:
    """
    Engine that reads frames from a video file using OpenCV 
    and streams them to a system Virtual Camera using PyVirtualCam.
    """
    def __init__(self, on_frame_callback: Optional[Callable[[np.ndarray], None]] = None,
                 on_status_change: Optional[Callable[[str, bool], None]] = None):
        self.video_path: Optional[str] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.cam: Optional[pyvirtualcam.Camera] = None
        
        self.is_streaming = False
        self.is_paused = False
        self.loop = True
        
        self.width = 1280
        self.height = 720
        self.fps = 30.0
        self.total_frames = 0
        self.current_frame_idx = 0
        self.duration = 0.0
        
        self.stream_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._seek_requested = None
        self._lock = threading.Lock()
        
        self.on_frame_callback = on_frame_callback
        self.on_status_change = on_status_change
        
        self.last_error_msg = ""

    def load_video(self, video_path: str) -> bool:
        """Loads video file and retrieves metadata (FPS, dimensions, total frames)."""
        self.stop_stream()
        
        with self._lock:
            self.video_path = video_path
            self.cap = cv2.VideoCapture(video_path)
            
            if not self.cap.isOpened():
                self.last_error_msg = f"Failed to open video file: {video_path}"
                return False
                
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            vid_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.fps = vid_fps if vid_fps > 0 else 30.0
            
            w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if w > 0 and h > 0:
                self.width = w
                self.height = h
                
            self.duration = self.total_frames / self.fps if self.fps > 0 else 0.0
            self.current_frame_idx = 0
            
            # Read first frame for preview
            ret, frame = self.cap.read()
            if ret and frame is not None:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if self.on_frame_callback:
                    self.on_frame_callback(rgb_frame)
            # Reset frame position to start
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return True

    def start_stream(self, target_width: Optional[int] = None, target_height: Optional[int] = None) -> bool:
        """Starts streaming the loaded video to PyVirtualCam in a background thread."""
        if not self.video_path or not self.cap or not self.cap.isOpened():
            self._notify_status("No video file loaded", False)
            return False
            
        if self.is_streaming:
            return True
            
        out_w = target_width if target_width else self.width
        out_h = target_height if target_height else self.height
        out_fps = self.fps
        
        try:
            # Try initializing PyVirtualCam device
            self.cam = pyvirtualcam.Camera(width=out_w, height=out_h, fps=out_fps, fmt=pyvirtualcam.PixelFormat.RGB)
            self._notify_status(f"Broadcasting to {self.cam.device} ({out_w}x{out_h} @ {out_fps:.1f} FPS)", True)
        except Exception as e:
            err_raw = str(e)
            if "not found" in err_raw or "No camera registered" in err_raw:
                err = "No Virtual Camera driver found on Windows.\nTo stream video as a webcam, please install OBS Studio (free) or Unity Capture driver."
            else:
                err = f"Virtual Camera Driver Error: {err_raw}"
            self.last_error_msg = err
            self._notify_status("Missing Virtual Camera Driver", False)
            return False

        self._stop_event.clear()
        self.is_streaming = True
        self.is_paused = False
        
        self.stream_thread = threading.Thread(target=self._stream_loop, args=(out_w, out_h), daemon=True)
        self.stream_thread.start()
        return True

    def stop_stream(self):
        """Stops the streaming thread and closes virtual camera handle."""
        self.is_streaming = False
        self._stop_event.set()
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=1.0)
            
        if self.cam:
            try:
                self.cam.close()
            except Exception:
                pass
            self.cam = None
            
        self._notify_status("Broadcasting stopped", False)

    def toggle_pause(self) -> bool:
        self.is_paused = not self.is_paused
        return self.is_paused

    def seek(self, frame_index: int):
        """Requests seeking to a specific frame number."""
        with self._lock:
            self._seek_requested = max(0, min(frame_index, self.total_frames - 1))

    def _stream_loop(self, target_w: int, target_h: int):
        """Background thread loop pushing RGB frames to PyVirtualCam buffer with timing sync."""
        frame_delay = 1.0 / self.fps
        
        while not self._stop_event.is_set() and self.is_streaming:
            start_time = time.perf_counter()
            
            # Handle user seek request
            if self._seek_requested is not None:
                with self._lock:
                    seek_frame = self._seek_requested
                    self._seek_requested = None
                    if self.cap:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, seek_frame)
                        self.current_frame_idx = seek_frame
            
            if self.is_paused:
                time.sleep(0.03)
                continue
                
            with self._lock:
                if not self.cap or not self.cap.isOpened():
                    break
                    
                ret, frame = self.cap.read()
                self.current_frame_idx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                
                if not ret or frame is None:
                    if self.loop:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        self.current_frame_idx = 0
                        ret, frame = self.cap.read()
                    else:
                        self.is_paused = True
                        continue

            if ret and frame is not None:
                # Resize if needed
                h, w = frame.shape[:2]
                if w != target_w or h != target_h:
                    frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)
                    
                # OpenCV uses BGR, PyVirtualCam expects RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Send to virtual camera driver
                if self.cam:
                    try:
                        self.cam.send(rgb_frame)
                    except Exception as e:
                        print("Send frame error:", e)
                        break

                # Send frame to UI preview callback
                if self.on_frame_callback:
                    self.on_frame_callback(rgb_frame)

            # Precise frame rate sleep timer
            elapsed = time.perf_counter() - start_time
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
                
        # Cleanup when loop exits
        if self.cam:
            try:
                self.cam.close()
            except Exception:
                pass
            self.cam = None
        self.is_streaming = False

    def _notify_status(self, msg: str, active: bool):
        if self.on_status_change:
            self.on_status_change(msg, active)

    def get_progress_seconds(self) -> float:
        if self.fps > 0:
            return self.current_frame_idx / self.fps
        return 0.0
