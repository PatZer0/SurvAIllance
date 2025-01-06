import os
import streamlit as st
from backend.data.dataloader import VideoDataLoader
from backend.rag.search_vdb_for_llm import rag_query
from logger import logger
from config import GlobalConfig

# Set the page title
st.set_page_config(page_title="SurvAIllence")

# Header for the web page
st.title("SurvAIllence")

# Initialize a logger for the Streamlit app (optional)
logger.setLevel("INFO")

# Data directory setup
data_dir = GlobalConfig.data_dir

# Function to load videos (for the background process)
def load_video_files():
    try:
        video_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.mp4')]
        logger.info(f'已发现 {len(video_files)} 个视频文件')
        logger.debug(f'已发现视频文件 {video_files}')
        return video_files
    except Exception as e:
        logger.error(f'无法找到视频文件! 错误: {e}')
        raise FileNotFoundError

# Video processing (if needed)
def process_video_files(video_files):
    for video_file in video_files:
        video_obj = VideoDataLoader(video_file, auto_process=True, reprocess=False)
        video_obj.add_event_to_database()

# Show the video files loading message (optional)
try:
    video_files = load_video_files()
    process_video_files(video_files)
except FileNotFoundError:
    st.error("视频文件未找到！请检查文件目录。")

# Query input
query_input = st.text_input("请输入查询内容:")

# Button to trigger the query
if st.button("查询"):
    if query_input:  # Check if the input is not empty
        # Show a loading spinner while waiting for the result
        with st.spinner('查询中...'):
            try:
                # Simulate query logic here
                query_result = rag_query(query_input)  # Pass the query input to the rag_query function

                # Display the query result
                st.write("查询结果:", query_result)
            except Exception as e:
                st.error(f"查询时发生错误: {e}")
    else:
        st.warning("请输入查询内容！")
