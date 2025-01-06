from datetime import datetime

from backend.vdb.vector_database import vdb_search_event
from backend.llm.text import text_generate_response_from_query_rag

from logger import logger


def get_user_query_input():
    user_query = input('请输入查询内容：')
    return user_query


def get_rag_result(user_query):
    rag_results = vdb_search_event(user_query)
    # 转为字符串
    result_str = str()
    for result in rag_results:
        result_str += f'搜索结果摘要：{result.page_content} \n\ \n'
    return result_str


def get_current_time():
    current_time = datetime.now()
    # 格式 '%Y-%m-%d-%H_%M_%S'
    current_time_str = current_time.strftime('%Y-%m-%d-%H_%M_%S')
    return current_time_str


def rag_query(user_query=None):
    while not user_query:
        logger.debug('未输入查询内容，获取用户输入')
        user_query = get_user_query_input()
    logger.debug(f'用户查询: {user_query}')
    rag_result = get_rag_result(user_query)
    text_response = text_generate_response_from_query_rag(user_query=user_query,
                                                          rag_result=rag_result,
                                                          current_time=get_current_time())
    logger.debug(f'查询结果: {text_response}')
    return text_response
