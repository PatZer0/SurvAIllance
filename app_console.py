# app_console.py

from backend.rag.search_vdb_for_llm import rag_query
from utils.search_and_load_videos import get_video_object_list

if __name__ == '__main__':
    video_objects = get_video_object_list()

    print(f'请注意：app_console 仅提供对数据库的查询功能。\n')

    while True:
        # 调用 rag_query 函数，stream 可以根据需要设置
        # 例如，设置 stream=True 以启用流式传输
        stream = True
        query_result, video_name_list = rag_query(with_video_list=True, stream=stream)

        if stream:
            print('查询中...')
            full_response = ''
            for part in query_result:
                if part.startswith("Error:"):
                    print(part)  # 直接打印错误信息
                    break
                print(part, end='', flush=True)  # 实时打印每个部分
                full_response += part
            print()  # 换行
            print(f'结果：{full_response}')
        else:
            print('查询中...')
            print(f'结果：{query_result}')

        print(f'使用的视频：{video_name_list}')

        # used_video_objects = [vo for vo in video_objects if vo.video_name in video_name_list]
        # print(used_video_objects)
