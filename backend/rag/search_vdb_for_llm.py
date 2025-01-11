import os
from datetime import datetime

from backend.vdb.vector_database import vdb_search_event
from backend.llm.text import text_generate_response_from_query_rag

from logger import logger
from config import GlobalConfig

def get_user_query_input():
    user_query = input('请输入查询内容：')
    return user_query


def get_rag_result(user_query):
    rag_results = vdb_search_event(user_query)
    # 转为字符串
    result_str = str()
    video_name_list = list()
    for result in rag_results:
        result_str += f'搜索结果摘要：{result.page_content} \n\ \n'
        video_name_list.append(result.metadata.get('video_name'))
    return result_str, video_name_list


def get_current_time():
    current_time = datetime.now()
    # 格式 '%Y-%m-%d-%H_%M_%S'
    current_time_str = current_time.strftime('%Y-%m-%d-%H_%M_%S')
    return current_time_str


def rag_query(user_query=None, stream=False, with_video_list=False):
    while not user_query:
        logger.debug('未输入查询内容，获取用户输入')
        user_query = get_user_query_input()
    logger.debug(f'用户查询: {user_query}')
    rag_result, video_name_list = get_rag_result(user_query)
    text_response = text_generate_response_from_query_rag(user_query=user_query,
                                                          rag_result=rag_result,
                                                          current_time=get_current_time(),
                                                          stream=stream)
    logger.debug(f'查询结果: {text_response}')
    logger.debug(f'使用的视频: {video_name_list}')
    if not with_video_list:
        return text_response
    else:
        return text_response, video_name_list