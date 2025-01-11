import sys
import cv2
import os
import subprocess

# 搜索当前文件夹下的视频文件
video_file_list = [file for file in os.listdir('.') if file.endswith('.mp4')]

# 让用户选择视频文件
if len(video_file_list) == 0:
    print('当前文件夹下没有视频文件')
    sys.exit(0)
elif len(video_file_list) == 1:
    video_file = video_file_list[0]
    # 组成绝对路径
    video_source = os.path.abspath(video_file)
else:
    print("可用的视频文件：")
    for i, file in enumerate(video_file_list, start=1):
        print(f"{i}. {file}")
    video_index = int(input('请输入序号：')) - 1
    video_file = video_file_list[video_index]
    video_source = f'./{video_file}'

# 启动 MediaMTX RTSP 服务器
mediamtx_exe = './mediamtx.exe'
if not os.path.exists(mediamtx_exe):
    print("未找到 mediamtx.exe，请确保文件在程序目录下")
    sys.exit(0)

print("启动 MediaMTX RTSP 服务器...")
mediamtx_process = subprocess.Popen([mediamtx_exe], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# 确保 RTSP 服务器启动成功
import time
time.sleep(2)  # 等待 RTSP 服务器启动

# FFmpeg RTSP 流推送命令
rtsp_url = 'rtsp://127.0.0.1:8554/test_stream'
ffmpeg_command = ['ffmpeg', '-re', '-stream_loop', '-1', '-i', video_source, '-c copy,' '-f', 'rtsp', rtsp_url]
print("开始推送视频流到 RTSP 服务器...")
ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

try:
    # 输出 RTSP 地址
    print(f"RTSP 流地址: {rtsp_url}")
    print("按 Ctrl+C 停止服务器和推流")
    ffmpeg_process.wait()
except KeyboardInterrupt:
    print("\n停止推流和服务器...")
finally:
    # 终止 FFmpeg 和 MediaMTX 进程
    ffmpeg_process.terminate()
    mediamtx_process.terminate()
