# frontend/app_flask.py

import os
import threading
import time
from datetime import datetime
from flask import Flask, Response, render_template, request, jsonify, send_file, send_from_directory
from backend.source.camera.recording import start_camera_recording, VideoRecordingConfig
from backend.rag.search_vdb_for_llm import rag_query
from backend.data.dataloader import VideoDataLoader
from logger import logger
from config import GlobalConfig

app = Flask(__name__)

# 全局变量
recorder = None
video_objects = []
events = []
events_lock = threading.Lock()

def initialize_recorder_and_data():
    global recorder, video_objects, events

    # 启动摄像头录制
    recorder = start_camera_recording()
    if recorder is None:
        logger.error("无法启动摄像头录制。")
        exit(1)
    else:
        logger.info("摄像头录制已启动，并在后台运行")

    # 初始化视频数据
    data_dir = GlobalConfig.data_dir
    try:
        video_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.mp4')]
        logger.info(f'已发现 {len(video_files)} 个视频文件')
        logger.debug(f'已发现视频文件 {video_files}')
    except Exception as e:
        logger.error(f'无法找到视频文件! 错误: {e}')
        raise FileNotFoundError

    for video_file in video_files:
        # 加载视频数据
        video_obj = VideoDataLoader(video_file, auto_process=False, reprocess=False)
        if not video_obj.detected:
            # 视频未检测过运动
            logger.info(f'正在检测视频 {video_obj.video_name} 的运动')
            video_obj._detect_motion()
            logger.info(f'视频 {video_obj.video_name} 运动检测完毕')
        if not video_obj.extracted:
            # 视频未提取过帧
            logger.info(f'正在提取视频 {video_obj.video_name} 的帧')
            video_obj._extract_frames()
            logger.info(f'视频 {video_obj.video_name} 提取帧完毕')
        if not video_obj.described:
            # 视频未生成过描述
            logger.info(f'正在生成视频 {video_obj.video_name} 的描述')
            video_obj._generate_descriptions()
            logger.info(f'视频 {video_obj.video_name} 生成描述完毕')

        video_obj.add_event_to_database()
        video_objects.append(video_obj)

    # 构建全局事件列表
    for vo in video_objects:
        for event in vo.events:
            # 确保 event.start_time 和 event.end_time 是 datetime 对象
            if isinstance(event.start_time, datetime) and isinstance(event.end_time, datetime):
                formatted_start = event.start_time.strftime('%Y年%m月%d日 %H时%M分%S秒')
                formatted_end = event.end_time.strftime('%Y年%m月%d日 %H时%M分%S秒')
            else:
                # 如果时间字段是字符串，尝试解析为 datetime 对象
                try:
                    start_dt = datetime.strptime(event.start_time, '%Y-%m-%d %H:%M:%S.%f')
                    end_dt = datetime.strptime(event.end_time, '%Y-%m-%d %H:%M:%S.%f')
                    formatted_start = start_dt.strftime('%Y年%m月%d日 %H时%M分%S秒')
                    formatted_end = end_dt.strftime('%Y年%m月%d日 %H时%M分%S秒')
                except ValueError:
                    logger.error(f"时间格式错误: {event.start_time}, {event.end_time}")
                    formatted_start = str(event.start_time)
                    formatted_end = str(event.end_time)

            events.append({
                'video_name': vo.video_name,
                'thumbnail_path': event.thumbnail_path,
                'description': event.description,
                'start_time': formatted_start,
                'end_time': formatted_end,
                'video_path': vo.video_path,
                'event_id': event.event_id  # 确保 event_id 存在
            })

    # 启动后台线程扫描新视频
    scan_thread = threading.Thread(target=scan_new_videos, daemon=True)
    scan_thread.start()

def scan_new_videos():
    """
    后台线程函数，每秒扫描一次 data_dir 是否有新视频文件。
    """
    global events, video_objects, recorder
    data_dir = GlobalConfig.data_dir
    processed_files = set([vo.video_path for vo in video_objects])

    while not recorder.stop_event.is_set():
        try:
            current_files = set([os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.mp4')])
            new_files = current_files - processed_files

            if new_files:
                logger.info(f'发现 {len(new_files)} 个新视频文件')
                for video_file in sorted(new_files):  # 按文件名排序，旧的先处理
                    logger.info(f'处理新视频文件: {video_file}')
                    video_obj = VideoDataLoader(video_file, auto_process=True, reprocess=False)
                    video_objects.append(video_obj)

                    # 添加事件到全局列表
                    with events_lock:
                        for event in video_obj.events:
                            # 确保 event.start_time 和 event.end_time 是 datetime 对象
                            if isinstance(event.start_time, datetime) and isinstance(event.end_time, datetime):
                                formatted_start = event.start_time.strftime('%Y年%m月%d日 %H时%M分%S秒')
                                formatted_end = event.end_time.strftime('%Y年%m月%d日 %H时%M分%S秒')
                            else:
                                # 如果时间字段是字符串，尝试解析为 datetime 对象
                                try:
                                    start_dt = datetime.strptime(event.start_time, '%Y-%m-%d %H:%M:%S.%f')
                                    end_dt = datetime.strptime(event.end_time, '%Y-%m-%d %H:%M:%S.%f')
                                    formatted_start = start_dt.strftime('%Y年%m月%d日 %H时%M分%S秒')
                                    formatted_end = end_dt.strftime('%Y年%m月%d日 %H时%M分%S秒')
                                except ValueError:
                                    logger.error(f"时间格式错误: {event.start_time}, {event.end_time}")
                                    formatted_start = str(event.start_time)
                                    formatted_end = str(event.end_time)

                            events.append({
                                'video_name': video_obj.video_name,
                                'thumbnail_path': event.thumbnail_path,
                                'description': event.description,
                                'start_time': formatted_start,
                                'end_time': formatted_end,
                                'video_path': video_obj.video_path,
                                'event_id': event.event_id  # 确保 event_id 存在
                            })

                    processed_files.add(video_file)

        except Exception as e:
            logger.error(f'扫描新视频文件时发生错误: {e}')

        time.sleep(1)

# 新增路由用于服务缓存中的缩略图
@app.route('/data/cache/<path:filename>')
def serve_cache(filename):
    """
    提供缓存目录中的文件访问。
    """
    return send_from_directory(VideoRecordingConfig.video_dir, filename)

@app.route('/')
def index():
    """返回主页"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """实时视频流路由"""
    return Response(generate_video_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_video_frames():
    """生成实时视频帧的生成器"""
    while True:
        frame = recorder.get_jpeg_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.1)

@app.route('/events')
def get_events():
    """获取事件列表的API路由"""
    with events_lock:
        return jsonify(events)

@app.route('/generate_response', methods=['POST'])
def generate_response():
    """
    接收用户查询并生成响应。
    支持流式传输以实时返回内容。
    """
    user_query = request.form.get('query')
    stream = True

    if not user_query:
        return jsonify({'error': '查询内容不能为空'}), 400

    # 正确传递参数
    logger.info(f'接收到用户查询: {user_query}, 流式传输: {stream}')
    logger.debug(f'流式传输已启用，将逐步返回结果')
    def generate():
        try:
            for part in rag_query(user_query=user_query, with_video_list=True, stream=True):
                yield part
        except Exception as e:
            logger.error(f"流式响应时发生错误: {e}")
            yield f"Error: {e}"
    return Response(generate(), mimetype='text/plain')

@app.route('/play_video/<int:event_id>')
def play_video(event_id):
    """
    播放指定事件的视频，从事件开始时间播放。
    """
    # 查找事件
    event = next((e for e in events if e['event_id'] == event_id), None)
    if not event:
        return "事件未找到", 404

    video_path = event['video_path']
    start_time = event['start_time']  # 格式化后的时间字符串

    if not os.path.exists(video_path):
        return "视频文件未找到", 404

    # 返回视频文件和开始时间
    return send_file(video_path, mimetype='video/mp4')

if __name__ == '__main__':
    # 启动初始化线程
    init_thread = threading.Thread(target=initialize_recorder_and_data, daemon=True)
    init_thread.start()

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
