import os
import logging
from datetime import datetime

class GlobalConfig:
    # 全局配置
    data_dir = 'data'


class VideoConfig:
    motion_threshold = 0.05
    min_interval_ms = 500
    max_silence_s = 2
    image_quality = 90

class LLMConfig:
    # 文本模型
    long_text_model = 'qwen2.5:7b'
    long_text_prompt = ('请基于这些从同一段监控视频中抽取的帧画面的文字描述，'
                        '用几句话简单地描述这期间发生的事情，就像连续发生的一样，'
                        '不要包含任何背景信息、格式，'
                        '不要包含画面、图片、镜头、视频等词语，'
                        '只输出连续一段话即可。')
    short_text_model = 'qwen2.5:7b'
    short_text_prompt = ('请用10个字总结这段监控内容，不要超过20个字，不要包含时间，'
                         '不要包含画面、图片、镜头、视频等词语，只输出一句话即可。')
    # 视觉模型
    visual_model = 'moondream:v2'
    # visual_model = 'llava:7b'
    visual_prompt = ('describe this surveillance image in the third person, '
                     'focus on objects, animals, humans, ')
    # 嵌入模型
    embedding_model = 'qwen2.5:7b'
    # 提问模型
    query_model = 'qwen2.5:7b'
    query_prompt = ('结合当前时间和数据库搜索结果，回答用户的问题。'
                    '过滤掉时间不符合的结果, 如果过滤后没有相关数据，直接输出“没有查询结果。"'
                    '当用户提到"我的"时，回答时请说"您的……"'
                    '回答格式: 根据搜索结果…'
                    '您提供的时间段为xxxx（根据已有时间信息，输出具体日期时间）'
                    '总结所有内容，然后简单介绍发生的事情。'
                    '<时间>发生了XX, XX, XX。'
                    '如果查询仅限于几天内，则使用昨天、前天、XX号这样的词。'
                    '如果查询跨越了月份，则使用具体日期。'
                    '注意总字数不要超过100字。尽可能简短容易理解。"')

class LogConfig:
    log_dir = "logs"
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    log_level = logging.INFO
    log_format = "[%(asctime)s] [%(levelname)s] %(message)s"

class RAGConfig:
    # 搜索结果数量
    top_k = 5

class DaemonConfig:
    scan_interval_s = 10

class ChromaDBConfig:
    persist_dir = 'data/database'


if __name__ == '__main__':
    print('This is a config file, not a script.')