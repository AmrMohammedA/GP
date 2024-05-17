#for modeling
import io
import random
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
# Clothing categories
sub_list = ["bottom", "foot", "top"]
top_list = [['Belts', 'Blazers', 'Dresses', 'Dupatta', 'Jackets', 'Kurtas', 'Kurtis', 'Lehenga Choli', 'Nehru Jackets', 'Rain Jacket', 'Rompers', 'Shirts', 'Shrug', 'Suspenders', 'Sweaters', 'Sweatshirts', 'Tops', 'Tshirts', 'Tunics', 'Waistcoat'],
            ['Boys', 'Girls', 'Men', 'Unisex', 'Women'],
            ['Black', 'Blue', 'Dark Blue', 'Dark Green', 'Dark Yellow', 'Green', 'Grey', 'Light Blue', 'Multi', 'Orange', 'Pink', 'Purple', 'Red', 'White', 'Yellow'],
            ['Fall', 'Spring', 'Summer', 'Winter'],
            ['Casual', 'Ethnic', 'Formal', 'Party', 'Smart Casual', 'Sports', 'Travel']]
bottom_list = [['Capris', 'Churidar', 'Jeans', 'Jeggings', 'Leggings', 'Patiala', 'Salwar', 'Salwar and Dupatta', 'Shorts', 'Skirts', 'Stockings', 'Swimwear', 'Tights', 'Track Pants', 'Tracksuits', 'Trousers'],
               ['Boys', 'Girls', 'Men', 'Unisex', 'Women'],
               ['Black', 'Blue', 'Dark Blue', 'Dark Green', 'Dark Yellow', 'Grey', 'Light Blue', 'Multi', 'Orange', 'Pink', 'Purple', 'Red', 'White', 'Yellow'],
               ['Fall', 'Spring', 'Summer', 'Winter'],
               ['Casual', 'Ethnic', 'Formal', 'Smart Casual', 'Sports']]
foot_list = [['Casual Shoes', 'Flats', 'Flip Flops', 'Formal Shoes', 'Heels', 'Sandals', 'Sports Sandals', 'Sports Shoes'],
             ['Boys', 'Girls', 'Men', 'Unisex', 'Women'],
             ['Black', 'Blue', 'Dark Blue', 'Dark Green', 'Dark Orange', 'Dark Yellow', 'Grey', 'Light Blue', 'Multi', 'Orange', 'Pink', 'Purple', 'Red', 'White', 'Yellow'],
             ['Fall', 'Spring', 'Summer', 'Winter'],
             ['Casual', 'Ethnic', 'Formal', 'Party', 'Smart Casual', 'Sports']]
# Function to convert RGB to color names
def convert_rgb_to_color_names(rgb_tuple):
    css3_db = CSS3_HEX_TO_NAMES
    names = []
    rgb_values = []
    for color_hex, color_name in css3_db.items():
        names.append(color_name)
        rgb_values.append(hex_to_rgb(color_hex))
    
    kdt_db = KDTree(rgb_values)
    distance, index = kdt_db.query(rgb_tuple)
    return names[index]

# Function to get dominant color from an image
def get_cloth_color(image):
    max_score = 0.0001
    dominant_color = None
    for count, (r, g, b) in image.getcolors(image.size[0]*image.size[1]):
        saturation = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)[1]
        y = min(abs(r*2104 + g*4130 + b*802 + 4096 + 131072) >> 13, 235)
        y = (y - 16.0) / (235 - 16)
        if y > 0.9:
            continue
        score = (saturation + 0.1) * count
        if score > max_score:
            max_score = score
            dominant_color = (r, g, b)
            
    return convert_rgb_to_color_names(dominant_color)

# Function for color classification
def color_classification(single_path):
    image = Image.open(single_path).convert('RGB')
    return get_cloth_color(image)

# Helper function for model prediction
def model_prediction(train_images, my_model, lelist):
    my_predictions = my_model.predict(train_images)
    result = []
    for i in range(len(lelist)):
        type_predicted_label = np.argmax(my_predictions[i][0])
        result.append(lelist[i][type_predicted_label])
    return result

# Function for single image classification
def image_classification(single_path):
    train_images = np.zeros((1, 80, 60, 3))
    img = cv2.imread(single_path)
    if img.shape != (80, 60, 3):
        img = image.load_img(single_path, target_size=(80, 60, 3))
    train_images[0] = img

    result2 = sub_list[np.argmax(sup_model.predict(train_images))]

    if result2 == "bottom":
        res = model_prediction(train_images, bottom_model, bottom_list)
    elif result2 == "top":
        res = model_prediction(train_images, top_model, top_list)
    elif result2 == "foot":
        res = model_prediction(train_images, foot_model, foot_list)
    res.append(single_path)
    res_str = f"{res[0]}, {res[1]}, {color_classification(single_path)}, {res[3]}, {res[4]}, {single_path}" 
    return (result2, res_str, res)

# Function to find complementary colors based on top color
import random
def find_combo_by_top(top_color_group, combotype):
    # Map color group values to their respective ranges
    def map_color_group(value):
        if value >= 12:
            return value - 12
        elif value < 0:
            return value + 12
        else:
            return value
    co = int(combotype/30)
    if top_color_group == 15: # If top color is multi
        bottom_color_group = random.choice([12, 13, 14])
        if bottom_color_group == 12: # If bottom color is black
            shoes_color_group = 13 # Set shoes to be white
        elif bottom_color_group == 13: # If bottom color is white
            shoes_color_group = random.choice([12, 13, 14]) # Set shoes to be black, white, or grey
        else: # If bottom color is grey
            shoes_color_group = random.choice([12, 13]) # Set shoes to be black or white
    elif top_color_group in [12, 13, 14]: # If top color is mono
        if top_color_group == 12:
            bottom_color_group = random.choice([12, 13])
            shoes_color_group = 13 if bottom_color_group == 12 else random.choice([12, 13])
        elif top_color_group == 13:
            bottom_color_group = random.choice([12, 13])
            shoes_color_group = 13 if bottom_color_group == 12 else 12
        else:
            bottom_color_group = random.choice([12, 13])
            shoes_color_group = random.choice([12, 13])
    else:
        bottom_color_group = map_color_group(top_color_group - co)
        shoes_color_group = map_color_group(top_color_group + co)

    return (map_color_group(bottom_color_group), map_color_group(shoes_color_group))
