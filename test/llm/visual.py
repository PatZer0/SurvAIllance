from backend.llm.visual import visual_explain_multiple_images, visual_explain_single_image

# image_paths_list = ['/home/patrick/project_nova/test/images/image1.jpg', '/home/patrick/project_nova/test/images/image2.jpg']
image_paths_list = ['/home/patrick/project_nova/data/output/test/event_6/frame1868.jpg']

response = visual_explain_multiple_images(image_paths_list, print_output=True)