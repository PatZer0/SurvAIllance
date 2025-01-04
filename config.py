# Configuration file for the project.

class VideoConfig:
    motion_threshold = 0.05
    min_interval_ms = 500
    max_silence_s = 2
    image_quality = 90

class LLMConfig:
    # 文本模型
    text_model = 'qwen2.5:7b'
    text_prompt = '请基于这些从同一段监控视频中抽取的帧画面的文字描述，用几句话简单地描述这期间发生的事情，就像连续发生的一样，不需要背景信息、格式，不要包含画面、图片、镜头、视频等词语，只输出连续一段话即可。'
    # 视觉模型
    visual_model = 'moondream:v2'
    visual_prompt = 'describe this surveillance image in the third person, focus on the content and mention nothing of the image itself'
