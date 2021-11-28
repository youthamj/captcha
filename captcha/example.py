from image import ImageCaptcha
import os

image = ImageCaptcha(fonts=['/arial.ttf'])
#add your required output directory instead
out_dir = '<your-output-dir>'


image.write('1234', os.path.join(out_dir, 'output.png'))


out_obj = image.generate_with_boxes('1234')

#save the output image
im = out_obj['final']
im.save(os.path.join(out_dir, 'output.png'), format='png')

#visualize bounding boxes on the image
im2 = out_obj['final_with_boxes']
im2.save(os.path.join(out_dir, 'output_with_boxes.png'), format='png')

#print bounding boxes
print(out_obj['bboxes'])