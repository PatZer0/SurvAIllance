from ollama import chat
from ollama import ChatResponse

LLM_MODEL = 'qwen2.5:7b'
# LLM_MODEL = 'qwen2.5-7b-instruct:latest'
LLM_PROMPT = '请基于这些从同一段监控视频中抽取的帧画面的文字描述，用几句话简单地描述这期间发生的事情，就像连续发生的一样，不需要背景信息、格式，不要包含画面、图片、镜头、视频等词语，只输出连续一段话即可。'

def text_generate_conclusion(list_of_responses, print_input=False, print_output=False):
    messages = []
    for i, response in enumerate(list_of_responses):
        messages.append({
            'role': 'assistant',
            'content': f'画面{i + 1}：{response}',
        })

    messages.append({
        'role': 'user',
        'content': LLM_PROMPT,
    })
    
    if print_input:
        print(messages)

    response: ChatResponse = chat(model=LLM_MODEL, messages=messages)
    
    if print_output:
        print(response.message.content)
    
    return response.message.content

def text_query_graph_rag():
    pass