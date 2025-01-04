from ollama import chat
from ollama import ChatResponse
from config import LLMConfig

LONG_LLM_PROMPT = LLMConfig.long_text_prompt
LONG_LLM_MODEL = LLMConfig.long_text_model

SHORT_LLM_PROMPT = LLMConfig.short_text_prompt
SHORT_LLM_MODEL = LLMConfig.short_text_model

def text_generate_conclusion(list_of_responses, print_input=False, print_output=False):
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
    
    if print_output:
        print(response.message.content)
    
    return response.message.content

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
    
    return response.message.content

def text_query_graph_rag():
    pass