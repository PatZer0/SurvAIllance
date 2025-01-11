import cv2
import json
import os
import time
from datetime import datetime

from config import VideoConfig

def detect_motion_in_video(
    video_path,
    video_start_time,       # 现实世界视频开始时间，例如 "2025-01-01 12:00:00" 
    output_json_dir,        # 输出JSON的文件夹
    motion_threshold=0.02,  # 运动检测阈值(相对于帧中像素总量的百分比)
    min_interval_ms=500,    # 最小间隔(ms)
    max_silence_s=2         # 超时间隔(s)
):
    """
    :param video_path:         输入视频文件路径
    :param video_start_time:   该视频在现实世界的开始时间（字符串或datetime对象）
    :param output_json_dir:    存放输出JSON的路径
    :param motion_threshold:   运动检测阈值(占比)，如0.02代表2%
    :param min_interval_ms:    两次记录事件的最小间隔，单位毫秒
    :param max_silence_s:      若超过此时间没有检测到运动则判定上一个事件结束，单位秒
    """
    # 将开始时间转为 datetime 类型，方便后续计算
    if isinstance(video_start_time, str):
        video_start_time_dt = datetime.strptime(video_start_time, "%Y-%m-%d %H:%M:%S")
    else:
        video_start_time_dt = video_start_time

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("无法打开视频文件:", video_path)
        return

    # 获取视频信息
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 背景分割器 (MOG2/BGSubtractorKNN等都可)
    back_sub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)

    # 事件相关变量
    events = []              # 保存所有事件
    current_event_frames = []# 当前事件包含的帧时间戳列表（视频内相对时间）
    last_motion_time = None  # 上一次检测到运动的时间（视频播放时间）
    last_save_time = 0       # 用于比较与上一次保存的时间是否大于 min_interval_ms

    # 将像素百分比阈值转换成一个整数值
    total_pixels = width * height
    pixel_threshold = total_pixels * motion_threshold

    # 帧遍历
    frame_index = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 当前帧相对视频开始位置的时间（秒）
        current_time_s = frame_index / fps

        # 应用背景分割器
        fg_mask = back_sub.apply(frame)

        # 对前景进行一些形态学操作，可以帮助减少噪点
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_DILATE, kernel)

        # 计算前景像素数量
        motion_pixels = (fg_mask > 0).sum()

        # 判断是否超过运动阈值
        if motion_pixels > pixel_threshold:
            # 与上一次保存记录的时间间隔(ms)
            now_ms = current_time_s * 1000
            if (now_ms - last_save_time) >= min_interval_ms:
                # 记录此帧相对时间
                current_event_frames.append(current_time_s)
                last_save_time = now_ms
            last_motion_time = current_time_s
        else:
            # 如果当前没有运动，但需要判断是否超过了max_silence_s
            if last_motion_time is not None:
                if (current_time_s - last_motion_time) > max_silence_s:
                    # 说明上一个事件结束
                    if current_event_frames:
                        events.append({
                            "frame_time": current_event_frames
                        })
                    # 重置当前事件
                    current_event_frames = []
                    last_motion_time = None

        frame_index += 1

    # 视频结束后，若还存在尚未保存的事件，则将其写入
    if current_event_frames:
        events.append({
            "frame_time": current_event_frames
        })

    cap.release()

    # 组装最终JSON数据
    result = {
        "video_start_time": video_start_time_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "events": []
    }
    # 将每个事件中帧的相对时间转换成真实世界的时间戳（可选）
    for e in events:
        real_timestamps = []
        for t in e["frame_time"]:
            # t是相对视频开始的秒数
            real_ts = video_start_time_dt.timestamp() + t
            real_dt = datetime.fromtimestamp(real_ts).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            real_timestamps.append(real_dt)
        result["events"].append({
            "frame_time": e["frame_time"],       # 保留相对帧时间
            "real_time": real_timestamps         # 可选，转换为真实时间
        })

    # 保存到JSON文件
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_json_path = os.path.join(output_json_dir, f"{video_name}.json")

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"检测完成，结果已保存至: {output_json_path}")
    return output_json_path
