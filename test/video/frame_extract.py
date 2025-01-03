from backend.video.frame_extract import extract_frames_from_video

video_path = "/home/patrick/project_nova/data/test.mp4"
json_path = "/home/patrick/project_nova/data/test.json"
output_dir = "/home/patrick/project_nova/data/frames"

extract_frames_from_video(video_path, json_path, output_dir)