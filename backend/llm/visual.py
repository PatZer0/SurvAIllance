from ollama import chat
from ollama import ChatResponse
from tqdm import tqdm

from config import LLMConfig

VLM_MODEL = LLMConfig.visual_model
VLM_PROMPT = LLMConfig.visual_prompt

def visual_explain_single_image(image_path, print_output=False):
    response: ChatResponse = chat(model=VLM_MODEL, messages=[
        {
            'role': 'user',
            'content': VLM_PROMPT,
            'images': [image_path],
        },
    ])
    if print_output:
        print(response.message.content)
    return response.message.content

def visual_explain_multiple_images(image_paths_list, print_output=False):
    responses = []
    for image_path in tqdm(image_paths_list, desc='视觉模型识别', unit='图片'):
        response = visual_explain_single_image(image_path, print_output=print_output)
        responses.append(response)

    return responses

if __name__ == '__main__':
    print('Running Test...')
    image_paths_list = ['/home/patrick/project_nova/test/images/image1.jpg', '/home/patrick/project_nova/test/images/image2.jpg']
    response = visual_explain_multiple_images(image_paths_list, print_output=True)