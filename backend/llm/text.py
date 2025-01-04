from ollama import chat
from ollama import ChatResponse
from config import LLMConfig

LLM_PROMPT = LLMConfig.text_prompt
LLM_MODEL = LLMConfig.text_model

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