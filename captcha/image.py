# coding: utf-8
"""
    captcha.image
    ~~~~~~~~~~~~~

    Generate Image CAPTCHAs, just the normal image CAPTCHAs you are using.
"""

import os
import random
from PIL import Image
from PIL import ImageFilter
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO
try:
    from wheezy.captcha import image as wheezy_captcha
except ImportError:
    wheezy_captcha = None

DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')
DEFAULT_FONTS = [os.path.join(DATA_DIR, 'DroidSansMono.ttf')]

if wheezy_captcha:
    __all__ = ['ImageCaptcha', 'WheezyCaptcha']
else:
    __all__ = ['ImageCaptcha']


table  =  []
for  i  in  range( 256 ):
    table.append( i * 1.97 )


class _Captcha(object):
    def generate(self, chars, format='png'):
        """Generate an Image Captcha of the given characters.

        :param chars: text to be generated.
        :param format: image file format
        """
        im = self.generate_image(chars)
        out = BytesIO()
        im.save(out, format=format)
        out.seek(0)
        return out

    def write(self, chars, output, format='png'):
        """Generate and write an image CAPTCHA data to the output.

        :param chars: text to be generated.
        :param output: output destination.
        :param format: image file format
        """
        obj = self.generate_image(chars)
        im = obj['final']
        return im.save(output, format=format)

    def generate_with_boxes(self, chars):
        """Generate and returns an image CAPTCHA  with its data in a dict.
        dict['final'] --> the image itself
        dict['bboxes'] --> a tuple for each bounding box in the form (character, x1, y1, width, height) of each bbox
        dict['final_with_boxes'] --> the image itself but with bounding boxes drawn around characters
        :param chars: text to be generated.
        """
        obj = self.generate_image(chars)
        return obj


class WheezyCaptcha(_Captcha):
    """Create an image CAPTCHA with wheezy.captcha."""
    def __init__(self, width=200, height=75, fonts=None):
        self._width = width
        self._height = height
        self._fonts = fonts or DEFAULT_FONTS

    def generate_image(self, chars):
        text_drawings = [
            wheezy_captcha.warp(),
            wheezy_captcha.rotate(),
            wheezy_captcha.offset(),
        ]
        fn = wheezy_captcha.captcha(
            drawings=[
                wheezy_captcha.background(),
                wheezy_captcha.text(fonts=self._fonts, drawings=text_drawings),
                wheezy_captcha.curve(),
                wheezy_captcha.noise(),
                wheezy_captcha.smooth(),
            ],
            width=self._width,
            height=self._height,
        )
        return fn(chars)


class ImageCaptcha(_Captcha):
    """Create an image CAPTCHA.

    Many of the codes are borrowed from wheezy.captcha, with a modification
    for memory and developer friendly.

    ImageCaptcha has one built-in font, DroidSansMono, which is licensed under
    Apache License 2. You should always use your own fonts::

        captcha = ImageCaptcha(fonts=['/path/to/A.ttf', '/path/to/B.ttf'])

    You can put as many fonts as you like. But be aware of your memory, all of
    the fonts are loaded into your memory, so keep them a lot, but not too
    many.

    :param width: The width of the CAPTCHA image.
    :param height: The height of the CAPTCHA image.
    :param fonts: Fonts to be used to generate CAPTCHA images.
    :param font_sizes: Random choose a font size from this parameters.
    """
    def __init__(self, width=160, height=60, fonts=None, font_sizes=None):
        self._width = width
        self._height = height
        self._fonts = fonts or DEFAULT_FONTS
        self._font_sizes = font_sizes or (42, 50, 56)
        self._truefonts = []

    @property
    def truefonts(self):
        if self._truefonts:
            return self._truefonts
        self._truefonts = tuple([
            truetype(n, s)
            for n in self._fonts
            for s in self._font_sizes
        ])
        return self._truefonts

    @staticmethod
    def create_noise_curve(image, color):
        w, h = image.size
        x1 = random.randint(0, int(w / 5))
        x2 = random.randint(w - int(w / 5), w)
        y1 = random.randint(int(h / 5), h - int(h / 5))
        y2 = random.randint(y1, h - int(h / 5))
        points = [x1, y1, x2, y2]
        end = random.randint(160, 200)
        start = random.randint(0, 20)
        Draw(image).arc(points, start, end, fill=color)
        return image

    @staticmethod
    def create_noise_dots(image, color, width=3, number=30):
        draw = Draw(image)
        w, h = image.size
        while number:
            x1 = random.randint(0, w)
            y1 = random.randint(0, h)
            draw.line(((x1, y1), (x1 - 1, y1 - 1)), fill=color, width=width)
            number -= 1
        return image

    def create_captcha_image(self, chars, color, background, for_training=True):
        """Create the CAPTCHA image itself.

        :param chars: text to be generated.
        :param color: color of the text.
        :param background: color of the background.

        The color should be a tuple of 3 numbers, such as (0, 255, 255).
        """
        image = Image.new('RGB', (self._width, self._height), background)
        draw = Draw(image)

        def _draw_character(c):
            font = random.choice(self.truefonts)
            w, h = draw.textsize(c, font=font)

            dx = random.randint(0, 4)
            dy = random.randint(0, 6)
            im = Image.new('RGBA', (w + dx, h + dy))
            Draw(im).text((dx, dy), c, font=font, fill=color)

            # rotate
            im = im.crop(im.getbbox())
            im = im.rotate(random.uniform(-30, 30), Image.BILINEAR, expand=1)

            # warp
            dx = w * random.uniform(0.1, 0.3)
            dy = h * random.uniform(0.2, 0.3)
            x1 = int(random.uniform(-dx, dx))
            y1 = int(random.uniform(-dy, dy))
            x2 = int(random.uniform(-dx, dx))
            y2 = int(random.uniform(-dy, dy))
            w2 = w + abs(x1) + abs(x2)
            h2 = h + abs(y1) + abs(y2)
            data = (
                x1, y1,
                -x1, h2 - y2,
                w2 + x2, h2 + y2,
                w2 - x2, -y1,
            )
            im = im.resize((w2, h2))
            im = im.transform((w, h), Image.QUAD, data)
            # print(x1, y1, x2, y2, w, h, w2, h2)
            return im

        images = []
        actual_char_inds = []
        ind = 0
        for c in chars:
            if random.random() > 0.5:
                images.append((' ', _draw_character(" ")))
                ind += 1
            actual_char_inds.append(ind)
            ind += 1
            images.append((c, _draw_character(c)))

        text_width = sum([im.size[0] for _, im in images])

        width = max(text_width, self._width)
        image = image.resize((width, self._height))
        if for_training:
            return_obj = {"char_onlys": [], "final": None, "bboxes":[]}
            blank = Image.new('RGB', (width, self._height), (255,255,255))

        average = int(text_width / len(chars))
        rand = int(0.25 * average)
        offset = int(average * 0.1)
        image_with_boxes = image.copy()
        for i, (c, im) in enumerate(images):
            w, h = im.size
            mask = im.convert('L').point(table)
            upper_left = (offset, int((self._height - h) / 2))
            upper_left_x, upper_left_y = upper_left
            
            if i in actual_char_inds and for_training:
                char_only_im = blank.copy()
                char_only_im.paste(im, upper_left, mask) 
                return_obj["char_onlys"].append(char_only_im)
            
            image.paste(im, upper_left, mask)
            image_with_boxes.paste(im, upper_left, mask)
            if c != ' ':
                return_obj["bboxes"].append((c, upper_left_x, upper_left_y, w, h))
                draw_boxes = Draw(image_with_boxes)
                draw_boxes.rectangle((upper_left_x, upper_left_y, upper_left_x+w, upper_left_y+h), outline ="red")
            offset = offset + w + random.randint(-rand, 0)

        if width > self._width:
            print("HIIIIIIIIIIIIIIIIIIII")
            image = image.resize((self._width, self._height))
            image_with_boxes = image_with_boxes.resize((self._width, self._height))
            bboxes = return_obj["bboxes"]
            resize_ratio_w = self._width/width
            for i, bbox in enumerate(bboxes):
                (bbox_c, bbox_upper_left_x, bbox_upper_left_y, bbox_w, bbox_h) = bbox 
                bboxes[i] = (bbox_c, bbox_upper_left_x*resize_ratio_w, bbox_upper_left_y, bbox_w*resize_ratio_w, bbox_h)
            return_obj["bboxes"] = bboxes

        if for_training:
            return_obj["final"] = image
            return_obj["final_with_boxes"] = image_with_boxes
            return return_obj
        else:
            return image

    def generate_image(self, chars, for_training=True):
        """Generate the image of the given characters.

        :param chars: text to be generated.
        """
        background = random_color(238, 255)
        color = random_color(10, 200, random.randint(220, 255))
        
        if for_training:
            return_obj = self.create_captcha_image(chars, color, background, for_training=for_training) 
            im = return_obj["final"]
            im_boxes = return_obj["final_with_boxes"]
        else:
            im = self.create_captcha_image(chars, color, background)
        self.create_noise_dots(im, color)
        self.create_noise_curve(im, color)
        im = im.filter(ImageFilter.SMOOTH)
        self.create_noise_dots(im_boxes, color)
        self.create_noise_curve(im_boxes, color)
        im_boxes = im_boxes.filter(ImageFilter.SMOOTH)

        if for_training:
            return_obj["final"] = im
            return_obj["final_with_boxes"] = im_boxes
            return return_obj
        else:
            return im


def random_color(start, end, opacity=None):
    red = random.randint(start, end)
    green = random.randint(start, end)
    blue = random.randint(start, end)
    if opacity is None:
        return (red, green, blue)
    return (red, green, blue, opacity)
