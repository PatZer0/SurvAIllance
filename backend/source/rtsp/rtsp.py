# realtime_video.py

import cv2
import threading
import time
import sys  # 导入 sys 模块以便在达到最大重试次数后退出程序
from config import RTSPClientConfig
from logger import logger

RTSP_URL = RTSPClientConfig.rtsp_url
RTSP_RETRY_DURATION_S = RTSPClientConfig.rtsp_retry_duration_s
RTSP_MAX_RETRIES = RTSPClientConfig.rtsp_max_retries


class RealTimeVideo:
    """
    RTSP 客户端类，使用 OpenCV 连接到 RTSP 流，实时获取视频帧。

    用法示例：
        video = RealTimeVideo()
        video.start()
        while True:
            frame = video.get_frame()
            if frame is not None:
                # 处理帧
                cv2.imshow('Frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        video.stop()
    """

    def __init__(self, rtsp_url=RTSP_URL, reconnect_delay=5):
        """
        初始化 RealTimeVideo 实例。

        :param rtsp_url: RTSP 流的 URL 地址。
        :param reconnect_delay: 重新连接的延迟时间（秒）。
        """
        self.rtsp_url = rtsp_url
        self.reconnect_delay = reconnect_delay
        self.capture = None
        self.thread = None
        self.stopped = False
        self.frame = None
        self.lock = threading.Lock()
        self.connected = False

        # 初始化重试参数
        self.retry_count = 0  # 当前重试次数

    def start(self):
        """
        启动视频捕捉线程。
        """
        if self.thread is not None and self.thread.is_alive():
            logger.warning("RealTimeVideo 已经在运行中。")
            return
        self.stopped = False
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        logger.info(f"RealTimeVideo 已启动，连接到 {self.rtsp_url}")

    def _update(self):
        """
        持续从 RTSP 流捕获帧。
        """
        while not self.stopped:
            if not self.connected:
                if self.retry_count >= RTSP_MAX_RETRIES:
                    logger.error(f"已达到最大重试次数 ({RTSP_MAX_RETRIES})，无法连接到 RTSP 流: {self.rtsp_url}")
                    self.stop()  # 停止线程和释放资源
                    sys.exit(1)  # 退出程序

                logger.info(f"尝试连接到 RTSP 流: {self.rtsp_url} (重试 {self.retry_count + 1}/{RTSP_MAX_RETRIES})")
                self.capture = cv2.VideoCapture(self.rtsp_url)
                if not self.capture.isOpened():
                    logger.error(f"无法连接到 RTSP 流: {self.rtsp_url}")
                    self.capture.release()
                    self.capture = None
                    self.retry_count += 1
                    logger.info(f"等待 {RTSP_RETRY_DURATION_S} 秒后重试...")
                    time.sleep(RTSP_RETRY_DURATION_S)
                    continue
                else:
                    self.connected = True
                    self.retry_count = 0  # 重置重试计数
                    logger.info(f"成功连接到 RTSP 流: {self.rtsp_url}")

            ret, frame = self.capture.read()
            if not ret:
                logger.warning("无法从 RTSP 流读取帧，尝试重新连接。")
                self.capture.release()
                self.capture = None
                self.connected = False
                self.retry_count += 1

                if self.retry_count >= RTSP_MAX_RETRIES:
                    logger.error(f"已达到最大重试次数 ({RTSP_MAX_RETRIES})，无法继续读取 RTSP 流: {self.rtsp_url}")
                    self.stop()  # 停止线程和释放资源
                    sys.exit(1)  # 退出程序

                logger.info(f"等待 {RTSP_RETRY_DURATION_S} 秒后重试...")
                time.sleep(RTSP_RETRY_DURATION_S)
                continue

            with self.lock:
                self.frame = frame

    def get_frame(self):
        """
        获取最新的帧。

        :return: 最新的视频帧（BGR 格式的 NumPy 数组）或 None 如果没有可用帧。
        """
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
            else:
                return None

    def stop(self):
        """
        停止视频捕捉线程并释放资源。
        """
        self.stopped = True
        if self.thread is not None:
            self.thread.join()
        if self.capture is not None:
            self.capture.release()
        logger.info("RealTimeVideo 已停止。")
