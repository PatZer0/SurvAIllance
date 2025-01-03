from ollama import chat
from ollama import ChatResponse

VLM_MODEL = 'moondream:v2'
# VLM_MODEL = 'llava:7b'
# VLM_PROMPT = 'describe this image in the third person, do not say image'
VLM_PROMPT = 'describe this surveillance image in the third person, focus on the content and mention nothing of the image itself'

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
    for image_path in image_paths_list:
        response = visual_explain_single_image(image_path, print_output=print_output)
        responses.append(response)

    return responses

if __name__ == '__main__':
    print('Running Test...')
    image_paths_list = ['/home/patrick/project_nova/test/images/image1.jpg', '/home/patrick/project_nova/test/images/image2.jpg']
    response = visual_explain_multiple_images(image_paths_list, print_output=True)