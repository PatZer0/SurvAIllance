# backend/camera/recording.py

import cv2
import threading
import time
import os
from collections import deque
from datetime import datetime

from backend.source.rtsp.rtsp import RealTimeVideo
from backend.data.dataloader import VideoDataLoader
from config import VideoRecordingConfig
from logger import logger

# 从配置文件加载参数
VIDEO_MOTION_DETECT_INTERVAL_MS = VideoRecordingConfig.video_motion_detect_interval_ms
VIDEO_DIR = VideoRecordingConfig.video_dir
VIDEO_CACHE_DURATION_S = VideoRecordingConfig.video_cache_duration_s
VIDEO_FPS = VideoRecordingConfig.video_fps
VIDEO_SIZE = tuple(VideoRecordingConfig.video_size)  # 确保是元组，例如 (1920, 1080)
VIDEO_CODEC = VideoRecordingConfig.video_codec
VIDEO_BITRATE_MBPS = VideoRecordingConfig.video_bitrate_mbps
VIDEO_RECORDING_WINDOW_S = VideoRecordingConfig.video_recording_window_s
MIN_MOTION_AREA = VideoRecordingConfig.min_motion_area  # 添加一个最小运动面积的配置


class VideoRecorder:
    """
    视频录制类，负责从 RTSP 流中获取视频帧，检测运动，并在检测到运动时录制视频。
    """

    def __init__(self):
        self.rtsp_client = RealTimeVideo()
        self.frame_buffer = deque(maxlen=int(VIDEO_CACHE_DURATION_S * VIDEO_FPS))
        self.buffer_lock = threading.Lock()

        self.recording = False
        self.recording_lock = threading.Lock()
        self.video_writer = None
        self.record_start_time = None

        self.last_motion_time = None
        self.motion_detected = False

        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

        # 初始化背景减除器
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)

    def start(self):
        """
        启动视频录制线程。
        """
        logger.info("启动 VideoRecorder")
        # 确保视频保存目录存在
        if not os.path.exists(VIDEO_DIR):
            os.makedirs(VIDEO_DIR)
            logger.info(f"创建视频保存目录: {VIDEO_DIR}")

        self.rtsp_client.start()
        self.thread.start()
        logger.info("VideoRecorder 已启动并在后台运行")

    def _run(self):
        """
        后台线程运行的主循环，负责帧获取、运动检测和视频录制。
        """
        logger.info("VideoRecorder 线程开始运行")
        while not self.stop_event.is_set():
            frame = self.rtsp_client.get_frame()
            if frame is not None:
                # 缓存最新帧
                with self.buffer_lock:
                    self.frame_buffer.append(frame.copy())

                # 运动检测
                motion = self._detect_motion(frame)

                current_time = time.time()

                if motion:
                    logger.debug("检测到运动")
                    self.last_motion_time = current_time
                    if not self.recording:
                        self._start_recording()
                else:
                    if self.recording and (current_time - self.last_motion_time) > VIDEO_RECORDING_WINDOW_S:
                        self._stop_recording()

                # 如果正在录制，写入当前帧
                if self.recording:
                    self._write_frame(frame)

            else:
                logger.warning("未获取到视频帧")
                time.sleep(VIDEO_MOTION_DETECT_INTERVAL_MS / 1000.0)

            # 根据检测间隔调整循环频率
            time.sleep(VIDEO_MOTION_DETECT_INTERVAL_MS / 1000.0)

        # 清理资源
        self._cleanup()
        logger.info("VideoRecorder 线程已停止")

    def _detect_motion(self, frame):
        """
        使用背景减除法检测运动。

        :param frame: 当前视频帧
        :return: 是否检测到运动
        """
        fg_mask = self.bg_subtractor.apply(frame)
        # 对掩码进行阈值化处理
        _, thresh = cv2.threshold(fg_mask, 244, 255, cv2.THRESH_BINARY)
        # 膨胀操作，填补孔洞
        thresh = cv2.dilate(thresh, None, iterations=2)
        # 查找轮廓
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < MIN_MOTION_AREA:
                continue
            return True  # 检测到足够大的运动

        return False

    def _start_recording(self):
        """
        开始录制视频，包含缓存中的过去 VIDEO_RECORDING_WINDOW_S 秒的内容。
        """
        with self.recording_lock:
            if self.recording:
                return  # 已经在录制中

            timestamp = datetime.now().strftime('%Y-%m-%d-%H_%M_%S')
            filename = os.path.join(VIDEO_DIR, f"{timestamp}.mp4")
            fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)
            bitrate = VIDEO_BITRATE_MBPS * 1000000  # 转换为 bps

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
            resized_frame = cv2.resize(frame, VIDEO_SIZE)
            self.video_writer.write(resized_frame)
        else:
            logger.error("视频写入器未初始化，无法写入帧")

    def _cleanup(self):
        """
        清理资源，停止录制和关闭视频捕捉。
        """
        logger.info("清理 VideoRecorder 资源")
        if self.recording and self.video_writer is not None:
            self.video_writer.release()
            logger.info("已释放视频写入器")
            self.recording = False
        self.rtsp_client.stop()

    def stop(self):
        """
        停止录制并终止后台线程。
        """
        logger.info("请求停止 VideoRecorder")
        self.stop_event.set()
        self.thread.join()
        logger.info("VideoRecorder 已停止")


def start_video_recording():
    """
    启动视频录制功能，以后台线程运行。

    其他程序可以调用此函数来启动运动检测和视频录制。
    """
    recorder = VideoRecorder()
    recorder.start()
    logger.info("视频录制已启动，并在后台运行")
    return recorder  # 返回实例以便外部控制（如停止）


if __name__ == '__main__':
    # 启动视频录制
    recorder = start_video_recording()