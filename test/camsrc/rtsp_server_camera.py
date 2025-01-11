import cv2
import subprocess

# 检查本机有几个摄像头
def check_device_cameras():
    camera_id = 0
    _available_cameras = []
    while True:
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            break
        _available_cameras.append(camera_id)
        camera_id += 1
        cap.release()
    return _available_cameras


available_cameras = check_device_cameras()
print(available_cameras)
# 让用户选择摄像头
user_input = input("请选择摄像头编号：")
video_source = int(user_input)

# FFmpeg RTSP 流推送命令
rtsp_url = 'rtsp://127.0.0.1:8554/test_stream'
ffmpeg_command = [
    'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo', '-pix_fmt', 'bgr24',
    '-s', '640x480', '-r', '30', '-i', '-', '-an', '-vcodec', 'libx264', '-preset', 'ultrafast',
    '-f', 'rtsp', rtsp_url
]

# 启动 FFmpeg 进程
ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

# 打开视频源（可以是文件或摄像头）
cap = cv2.VideoCapture(video_source)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # 通过管道将帧数据传输给 FFmpeg 进程
    ffmpeg_process.stdin.write(frame.tobytes())

cap.release()
ffmpeg_process.stdin.close()
ffmpeg_process.wait()
