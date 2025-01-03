import os
import json
import cv2
from math import floor

def extract_frames_from_video(
    video_path,
    json_path,
    output_dir,
    image_quality=90
):
    """
    :param video_path:    原始视频文件路径
    :param json_path:     对应的JSON文件路径
    :param output_dir:    提取到的帧保存文件夹
    :param image_quality: 保存图像的质量
    """
    # 读取JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 视频名(不带后缀)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    # 创建输出目录: xxx/视频文件名
    video_output_dir = os.path.join(output_dir, video_name)
    if not os.path.exists(video_output_dir):
        os.makedirs(video_output_dir, exist_ok=True)

    # 打开视频
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    events = data.get("events", [])
    for idx, event in enumerate(events, start=1):
        # 为每个事件创建独立文件夹
        event_dir = os.path.join(video_output_dir, f"event_{idx}")
        os.makedirs(event_dir, exist_ok=True)

        frame_time_list = event.get("frame_time", [])
        for frame_t in frame_time_list:
            # frame_t 是相对视频开始的秒数，计算对应帧号
            frame_idx = int(floor(frame_t * fps))  
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue

            # 保存 jpg
            # 格式 frameXXXX.jpg
            output_name = f"frame{frame_idx:04d}.jpg"
            output_path = os.path.join(event_dir, output_name)
            cv2.imwrite(output_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), image_quality])

    cap.release()
    print(f"帧提取完成，结果保存在: {video_output_dir}")
    return video_output_dir
