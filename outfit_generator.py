#for modeling
import io
import random
import traceback
from keras.preprocessing import  image
#for read and show images
import matplotlib.pyplot as plt
import cv2                                                          
import matplotlib.image as mpimg
#for save and load models
import tensorflow as tf
from keras.models import load_model 
import numpy as np
#for color classification
import colorsys                                                     
import PIL.Image as Image

from scipy.spatial import KDTree
from webcolors import (
   CSS3_HEX_TO_NAMES,
    hex_to_rgb
)
   
    

sup_model = tf.keras.models.load_model('SUP')
top_model = tf.keras.models.load_model('TOP')
bottom_model = tf.keras.models.load_model('BOTTOM')
foot_model = tf.keras.models.load_model('FOOT')

# Define lists for classification
sub_list = ["bottom", "foot", "top"]
top_list = [['Belts', 'Blazers', 'Dresses', 'Dupatta', 'Jackets', 'Kurtas', 'Kurtis', 'Lehenga Choli', 'Nehru Jackets', 'Rain Jacket',
             'Rompers', 'Shirts', 'Shrug', 'Suspenders', 'Sweaters', 'Sweatshirts', 'Tops', 'Tshirts', 'Tunics', 'Waistcoat'],
            ['Boys', 'Girls', 'Men', 'Unisex', 'Women'],
            ['Black', 'Blue', 'Dark Blue', 'Dark Green', 'Dark Yellow', 'Green', 'Grey', 'Light Blue', 'Multi', 'Orange', 'Pink', 'Purple', 'Red', 'White', 'Yellow'],
            ['Fall', 'Spring', 'Summer', 'Winter'],
            ['Casual', 'Ethnic', 'Formal', 'Party', 'Smart Casual', 'Sports', 'Travel']]
bottom_list = [['Capris', 'Churidar', 'Jeans', 'Jeggings', 'Leggings', 'Patiala', 'Salwar', 'Salwar and Dupatta', 'Shorts', 'Skirts', 'Stockings',
                'Swimwear', 'Tights', 'Track Pants', 'Tracksuits', 'Trousers'],
               ['Boys', 'Girls', 'Men', 'Unisex', 'Women'],
               ['Black', 'Blue', 'Dark Blue', 'Dark Green', 'Dark Yellow', 'Grey', 'Light Blue', 'Multi', 'Orange', 'Pink', 'Purple', 'Red', 'White', 'Yellow'],
               ['Fall', 'Spring', 'Summer', 'Winter'],
               ['Casual', 'Ethnic', 'Formal', 'Smart Casual', 'Sports']]
foot_list = [['Casual Shoes', 'Flats', 'Flip Flops', 'Formal Shoes', 'Heels', 'Sandals', 'Sports Sandals', 'Sports Shoes'],
             ['Boys', 'Girls', 'Men', 'Unisex', 'Women'],
             ['Black', 'Blue', 'Dark Blue', 'Dark Green', 'Dark Orange', 'Dark Yellow', 'Grey', 'Light Blue', 'Multi', 'Orange', 'Pink', 'Purple', 'Red', 'White', 'Yellow'],
             ['Fall', 'Spring', 'Summer', 'Winter'],
             ['Casual', 'Ethnic', 'Formal', 'Party', 'Smart Casual', 'Sports']]

def convert_rgb_to_names(rgb_tuple):
    """Translate RGB to their respective names in CSS3."""
    css3_db = CSS3_HEX_TO_NAMES
    names, rgb_values = zip(*[(name, hex_to_rgb(hex)) for hex, name in css3_db.items()])
    kdt_db = KDTree(rgb_values)
    distance, index = kdt_db.query(rgb_tuple)
    return names[index]

def get_dominant_color(image):
    """Recognize the dominant color of an image."""
    max_score = 0.0001
    dominant_color = None
    for count, (r, g, b) in image.getcolors(image.size[0] * image.size[1]):
        saturation = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)[1]
        y = min(abs(r * 2104 + g * 4130 + b * 802 + 4096 + 131072) >> 13, 235)
        y = (y - 16.0) / (235 - 16)
        if y > 0.9:
            continue
        score = (saturation + 0.1) * count
        if score > max_score:
            max_score = score
            dominant_color = (r, g, b)
    return convert_rgb_to_names(dominant_color)

def color_classification(image_data):
    """Classify the color of an image."""
    image = Image.fromarray(image_data)
    return get_dominant_color(image)

def single_helper(train_images, model, lelist):
    """Use pre-trained model to predict and return the result as a list."""
    predictions = model.predict(train_images)
    return [lelist[i][np.argmax(predictions[i][0])] for i in range(len(lelist))]

def image_classification(image_data, url):
    """Perform classification and return the result with the image URL."""
    try:
        if image_data.shape != (80, 60, 3):
            image_data = cv2.resize(image_data, (60, 80))

        train_images = np.zeros((1, 80, 60, 3))
        train_images[0] = image_data

        category = sub_list[np.argmax(sup_model.predict(train_images))]

        if category == "top":
            result = single_helper(train_images, top_model, top_list)
        elif category == "bottom":
            result = single_helper(train_images, bottom_model, bottom_list)
        elif category == "foot":
            result = single_helper(train_images, foot_model, foot_list)

        color = color_classification(image_data)
        result.append(url)
        result_str = f"{result[0]}, {result[1]}, {color}, {result[3]}, {result[4]}, {url}"

        return category, result_str, result

    except Exception as e:
        print("Error in single_classification:", e)
        traceback.print_exc()
        return None

def find_combo_by_top(top_color_group, combotype):
    """Recommend colors based on a seed color and given angle in a color wheel."""
    co = int(combotype / 30)
    if top_color_group == 15:  # Multi-color
        bottom_color_group = random.choice([12, 13, 14])
        shoes_color_group = 13 if bottom_color_group == 12 else random.choice([12, 13])
    elif top_color_group in [12, 13, 14]:  # Monochrome colors
        bottom_color_group = random.choice([12, 13])
        shoes_color_group = 13 if bottom_color_group == 12 else random.choice([12, 13])
    else:
        bottom_color_group = random.choice([top_color_group - co, top_color_group + co])
        shoes_color_group = top_color_group + co if bottom_color_group == top_color_group - co else top_color_group - co

    bottom_color_group = (bottom_color_group + 6) % 12 if bottom_color_group < 0 else bottom_color_group
    shoes_color_group = (shoes_color_group + 6) % 12 if shoes_color_group < 0 else shoes_color_group

    return bottom_color_group, shoes_color_group
