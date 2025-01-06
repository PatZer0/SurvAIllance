import os

from backend.data.dataloader import VideoDataLoader
from backend.vdb.vector_database import vdb_search_event
from backend.rag.search_vdb_for_llm import rag_query

from logger import logger
from config import GlobalConfig

if __name__ == '__main__':
    data_dir = GlobalConfig.data_dir
    try:
        video_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.mp4')]
        logger.info(f'已发现 {len(video_files)} 个视频文件')
        logger.debug(f'已发现视频文件 {video_files}')
    except Exception as e:
        logger.error(f'无法找到视频文件! 错误: {e}')
        raise FileNotFoundError

    for video_file in video_files:
        video_obj = VideoDataLoader(video_file, auto_process=True, reprocess=False)
        video_obj.add_event_to_database()

    while True:
        rag_query()

