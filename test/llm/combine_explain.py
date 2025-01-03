import os

from backend.llm.visual import visual_explain_multiple_images
from backend.llm.text import text_generate_conclusion

image_folder_path = '/home/patrick/project_nova/data/output/test/event_2'

# Find all the jpg files in the folder and arrange them in a list
image_paths_list = []
for file_name in os.listdir(image_folder_path):
    if file_name.endswith('.jpg'):
        image_paths_list.append(os.path.join(image_folder_path, file_name))

# Visual Explanation
visual_responses = visual_explain_multiple_images(image_paths_list, print_output=True)

# Text Generation
text_generate_conclusion(visual_responses, print_output=True)
