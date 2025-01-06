from ollama import chat
from ollama import ChatResponse
from config import LLMConfig
from logger import logger

LONG_LLM_PROMPT = LLMConfig.long_text_prompt
LONG_LLM_MODEL = LLMConfig.long_text_model

SHORT_LLM_PROMPT = LLMConfig.short_text_prompt
SHORT_LLM_MODEL = LLMConfig.short_text_model

QUERY_MODEL = LLMConfig.query_model
QUERY_MODEL_PROMPT = LLMConfig.query_prompt


def text_generate_conclusion(list_of_responses, start_time, end_time, print_input=False, print_output=False):
    messages = []
    for i, response in enumerate(list_of_responses):
        messages.append({
            'role': 'assistant',
            'content': f'画面{i + 1}：{response}',
        })

    messages.append({
        'role': 'user',
        'content': LONG_LLM_PROMPT,
    })

    if print_input:
        print(messages)

    response: ChatResponse = chat(model=LONG_LLM_MODEL, messages=messages)

    time_text = f'开始于{start_time}，结束于{end_time}：'
    output_text = f'{time_text} {response.message.content}'

    if print_output:
        print(output_text)

    logger.debug(f'文本总结: {output_text}')

    return output_text


def text_generate_short_conclusion(text, print_input=False, print_output=False):
    if print_input:
        print(text)

    response: ChatResponse = chat(model=SHORT_LLM_MODEL, messages=[{
        'role': 'user',
        'content': text,
    }, {
        'role': 'user',
        'content': SHORT_LLM_PROMPT,
    }])

    if print_output:
        print(response.message.content)
    logger.debug(f'文本简短总结: {response.message.content}')
    return response.message.content


def text_generate_response_from_query_rag(user_query, rag_result, current_time):
    messages = list()
    messages.append({
        'role': 'system',
        'content': rag_result,
    })
    messages.append({
        'role': 'system',
        'content': f'当前时间是{current_time}',
        })
    messages.append({
        'role': 'user',
        'content': user_query,
    })
    logger.debug(f'查询消息: {messages}')
    response: ChatResponse = chat(QUERY_MODEL, messages=messages)
    logger.debug(f'查询响应: {response.message.content}')
    return response.message.content
