from backend.video.motion_detect import detect_motion_in_video

video_path = "/home/patrick/project_nova/data/test.mp4"
video_start_time = "2024-12-31 00:00:00"
output_json_dir = "/home/patrick/project_nova/data/"

detect_motion_in_video(video_path, video_start_time, output_json_dir)