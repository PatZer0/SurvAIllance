import os

from backend.data.dataloader import VideoDataLoader
from config import GlobalConfig
from logger import logger

data_dir = GlobalConfig.data_dir

def get_video_object_list():
    try:
        video_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.mp4')]
        logger.info(f'已发现 {len(video_files)} 个视频文件')
        logger.debug(f'已发现视频文件 {video_files}')
    except Exception as e:
        logger.error(f'无法找到视频文件! 错误: {e}')
        raise FileNotFoundError

    video_objects = []

    for video_file in video_files:
        video_obj = VideoDataLoader(video_file, auto_process=True, reprocess=False)
        video_obj.add_event_to_database()
        video_objects.append(video_obj)

    return video_objects