import os
import logging
from datetime import datetime

class VideoConfig:
    motion_threshold = 0.05
    min_interval_ms = 500
    max_silence_s = 2
    image_quality = 90

class LLMConfig:
    # 文本模型
    long_text_model = 'qwen2.5:7b'
    long_text_prompt = '请基于这些从同一段监控视频中抽取的帧画面的文字描述，用几句话简单地描述这期间发生的事情，就像连续发生的一样，不需要背景信息、格式，不要包含画面、图片、镜头、视频等词语，只输出连续一段话即可。'
    short_text_model = 'qwen2.5:7b'
    short_text_prompt = '请用10个字总结这段监控内容，不要超过20个字，不要包含画面、图片、镜头、视频等词语，只输出一句话即可。'
    # 视觉模型
    visual_model = 'moondream:v2'
    visual_prompt = 'describe this surveillance image in the third person, focus on the content and mention nothing of the image itself'

class LogConfig:
    log_dir = "logs"
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    log_level = logging.DEBUG
    log_format = "[%(asctime)s] [%(levelname)s] %(message)s"

class DaemonConfig:
    scan_interval_s = 10

class GraphRAGConfig:
    pass