# backend/camera/recording.py

import cv2
import threading
import time
import os
from collections import deque
from datetime import datetime

from config import CameraConfig, VideoRecordingConfig
from logger import logger

# 从配置文件加载参数
COLD_START_WAIT_S = VideoRecordingConfig.cold_start_wait_s
CAMERA_ID = CameraConfig.camera_id
VIDEO_MOTION_DETECT_INTERVAL_MS = VideoRecordingConfig.video_motion_detect_interval_ms
VIDEO_DIR = VideoRecordingConfig.video_dir
VIDEO_CACHE_DURATION_S = VideoRecordingConfig.video_cache_duration_s
VIDEO_FPS = VideoRecordingConfig.video_fps
VIDEO_SIZE = tuple(VideoRecordingConfig.video_size)  # 确保是元组，例如 (1920, 1080)
VIDEO_CODEC = VideoRecordingConfig.video_codec
VIDEO_BITRATE_MBPS = VideoRecordingConfig.video_bitrate_mbps
VIDEO_RECORDING_WINDOW_S = VideoRecordingConfig.video_recording_window_s
MIN_MOTION_AREA = VideoRecordingConfig.min_motion_area  # 添加一个最小运动面积的配置

# 新增的运动检测灵敏度参数
MOTION_BG_HISTORY = VideoRecordingConfig.motion_bg_history
MOTION_BG_VARTHRESHOLD = VideoRecordingConfig.motion_bg_varThreshold
MOTION_DETECTSHADOWS = VideoRecordingConfig.motion_detectShadows
MOTION_THRESH_VAL = VideoRecordingConfig.motion_thresh_val
MOTION_DILATE_ITERATIONS = VideoRecordingConfig.motion_dilate_iterations


class CameraRecorder:
    """
    摄像头录制类，负责从本地摄像头获取视频帧，检测运动，并在检测到运动时录制视频。
    同时提供获取当前摄像头画面的功能，便于实时显示在前端。
    """

    def __init__(self):
        self.capture = cv2.VideoCapture(CAMERA_ID)
        if not self.capture.isOpened():
            logger.error(f"无法打开摄像头 ID: {CAMERA_ID}")
            raise ValueError(f"无法打开摄像头 ID: {CAMERA_ID}")

        # 设置摄像头参数（可选）
        self.capture.set(cv2.CAP_PROP_FPS, VIDEO_FPS)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, VIDEO_SIZE[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_SIZE[1])

        self.frame_buffer = deque(maxlen=int(VIDEO_CACHE_DURATION_S * VIDEO_FPS))
        self.buffer_lock = threading.Lock()

        self.recording = False
        self.recording_lock = threading.Lock()
        self.video_writer = None
        self.record_start_time = None

        self.last_motion_time = None

        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

        # 初始化背景减除器，使用配置文件中的参数
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=MOTION_BG_HISTORY,
            varThreshold=MOTION_BG_VARTHRESHOLD,
            detectShadows=MOTION_DETECTSHADOWS
        )

        # 当前帧，用于实时显示
        self.current_frame = None
        self.current_frame_lock = threading.Lock()

    def start(self):
        """
        启动摄像头录制线程。
        """
        logger.info("启动 CameraRecorder")
        # 确保视频保存目录存在
        if not os.path.exists(VIDEO_DIR):
            os.makedirs(VIDEO_DIR)
            logger.info(f"创建视频保存目录: {VIDEO_DIR}")

        self.thread.start()

        # 等待冷启动时间
        logger.info(f"等待 {COLD_START_WAIT_S} 秒以进行冷启动")
        time.sleep(COLD_START_WAIT_S)
        logger.info(f"冷启动完成，开始运动检测")

    def _run(self):
        """
        后台线程运行的主循环，负责帧获取、运动检测和视频录制。
        使用时间控制机制分离帧捕捉和运动检测的频率。
        """
        logger.info("CameraRecorder 线程开始运行")
        frame_interval = 1.0 / VIDEO_FPS  # 每帧的时间间隔
        next_frame_time = time.time()
        next_motion_time = time.time()

        while not self.stop_event.is_set():
            current_time = time.time()

            # 捕捉帧
            if current_time >= next_frame_time:
                ret, frame = self.capture.read()
                if not ret:
                    logger.warning("无法从摄像头读取帧")
                    next_frame_time += frame_interval
                    continue

                # 更新当前帧
                with self.current_frame_lock:
                    self.current_frame = frame.copy()

                # 缓存最新帧
                with self.buffer_lock:
                    self.frame_buffer.append(frame.copy())

                # 如果正在录制，写入当前帧
                if self.recording:
                    self._write_frame(frame)

                next_frame_time += frame_interval

            # 运动检测
            if current_time >= next_motion_time:
                with self.buffer_lock:
                    if len(self.frame_buffer) > 0:
                        latest_frame = self.frame_buffer[-1].copy()
                    else:
                        latest_frame = None

                if latest_frame is not None:
                    motion = self._detect_motion(latest_frame)
                    if motion:
                        logger.debug("检测到运动")
                        self.last_motion_time = current_time
                        if not self.recording:
                            self._start_recording()
                    else:
                        if self.recording and (current_time - self.last_motion_time) > VIDEO_RECORDING_WINDOW_S:
                            self._stop_recording()

                next_motion_time += VIDEO_MOTION_DETECT_INTERVAL_MS / 1000.0

            # 确保循环不会过快运行
            time.sleep(0.001)

        # 清理资源
        self._cleanup()
        logger.info("CameraRecorder 线程已停止")

    def _detect_motion(self, frame):
        """
        使用背景减除法检测运动。

        :param frame: 当前视频帧
        :return: 是否检测到运动
        """
        fg_mask = self.bg_subtractor.apply(frame)
        _, thresh = cv2.threshold(fg_mask, MOTION_THRESH_VAL, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=MOTION_DILATE_ITERATIONS)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        logger.debug(f"检测到 {len(contours)} 个轮廓")

        for contour in contours:
            area = cv2.contourArea(contour)
            logger.debug(f"轮廓面积: {area}")
            if area < MIN_MOTION_AREA:
                continue
            return True  # 检测到足够大的运动

        return False

    def _start_recording(self):
        """
        开始录制视频，包含缓存中的过去 VIDEO_CACHE_DURATION_S 秒的内容。
        """
        with self.recording_lock:
            if self.recording:
                return  # 已经在录制中

            timestamp = datetime.now().strftime('%Y-%m-%d-%H_%M_%S')
            filename = os.path.join(VIDEO_DIR, f"{timestamp}.mp4")
            fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)

            self.video_writer = cv2.VideoWriter(
                filename,
                fourcc,
                VIDEO_FPS,
                VIDEO_SIZE
            )

            if not self.video_writer.isOpened():
                logger.error(f"无法打开视频写入器，无法录制视频: {filename}")
                self.video_writer = None
                return

            logger.info(f"开始录制视频: {filename}")

            # 写入缓存中的帧
            with self.buffer_lock:
                for buffered_frame in list(self.frame_buffer):
                    resized_frame = cv2.resize(buffered_frame, VIDEO_SIZE)
                    self.video_writer.write(resized_frame)

            self.recording = True
            self.record_start_time = time.time()

    def _stop_recording(self):
        """
        停止视频录制。
        """
        with self.recording_lock:
            if not self.recording:
                return  # 未在录制中

            logger.info("停止录制视频")
            self.video_writer.release()
            self.video_writer = None
            self.recording = False
            self.record_start_time = None

    def _write_frame(self, frame):
        """
        将帧写入视频文件。

        :param frame: 当前视频帧
        """
        if self.video_writer is not None:
            try:
                resized_frame = cv2.resize(frame, VIDEO_SIZE)
                self.video_writer.write(resized_frame)
            except Exception as e:
                logger.error(f"写入帧时发生错误: {e}")
        else:
            logger.error("视频写入器未初始化，无法写入帧")

    def _cleanup(self):
        """
        清理资源，停止录制和关闭视频捕捉。
        """
        logger.info("清理 CameraRecorder 资源")
        if self.recording and self.video_writer is not None:
            self.video_writer.release()
            logger.info("已释放视频写入器")
            self.recording = False
        if self.capture.isOpened():
            self.capture.release()
            logger.info("已释放摄像头资源")

    def stop(self):
        """
        停止录制并终止后台线程。
        """
        logger.info("请求停止 CameraRecorder")
        self.stop_event.set()
        self.thread.join()
        logger.info("CameraRecorder 已停止")

    def get_jpeg_frame(self):
        """
        获取当前摄像头画面的 JPEG 编码数据。

        :return: JPEG 编码的图像数据（bytes）或 None 如果没有可用帧。
        """
        with self.current_frame_lock:
            if self.current_frame is not None:
                # 将BGR格式转换为RGB
                rgb_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
                # 编码为JPEG
                ret, jpeg = cv2.imencode('.jpg', rgb_frame)
                if ret:
                    return jpeg.tobytes()
                else:
                    logger.error("JPEG编码失败")
                    return None
            else:
                return None


def start_camera_recording():
    """
    启动摄像头录制功能，以后台线程运行。

    其他程序可以调用此函数来启动运动检测和视频录制。
    """
    try:
        recorder = CameraRecorder()
        recorder.start()
        logger.info("摄像头录制已启动，并在后台运行")
        return recorder  # 返回实例以便外部控制（如停止）
    except Exception as e:
        logger.error(f"启动摄像头录制失败: {e}")
        return None


if __name__ == '__main__':
    logger.warning('您正在以测试模式运行摄像头录制功能，正确的方法是在其他程序中调用 start_camera_recording() 函数。')
    recorder = start_camera_recording()
    while True:
        time.sleep(1)