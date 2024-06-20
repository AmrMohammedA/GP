import io
import random
import traceback
import numpy as np
import colorsys
import cv2
import tensorflow as tf
from keras.models import load_model
from webcolors import hex_to_rgb, rgb_to_hex
from PIL import Image
from scipy.spatial import KDTree
from webcolors import hex_to_rgb
from sklearn.cluster import KMeans
from colors import CSS3_HEX_TO_NAMES  # Import color definitions

# Load models
sup_model = load_model('SUP')
top_model = load_model('TOP')
bottom_model = load_model('BOTTOM')
foot_model = load_model('FOOT')

# Define lists for classification
sub_list = ["bottom", "foot", "top"]
top_list = [['Belts', 'Blazers', 'Dresses', 'Dupatta', 'Jackets', 'Kurtas', 'Kurtis', 'Lehenga Choli', 'Nehru Jackets', 'Rain Jacket', 'Rompers', 'Shirts', 'Shrug', 'Suspenders', 'Sweaters', 'Sweatshirts', 'Tops', 'Tshirts', 'Tunics', 'Waistcoat'],
            ['Boys', 'Girls', 'Men', 'Unisex', 'Women'],
            ['Black', 'Blue', 'Navy Blue', 'Sky Blue', 'Dark Blue', 'Light Blue', 'Dark Green', 'Olive Green', 'Light Green', 'Dark Yellow', 'Light Yellow', 'Green', 'Grey', 'Light Grey', 'Dark Grey', 'Multi', 'Orange', 'Dark Orange', 'Peach', 'Pink', 'Hot Pink', 'Purple', 'Lavender', 'Red', 'Maroon', 'White', 'Off White', 'Yellow', 'Beige', 'Brown', 'Dark Brown', 'Light Brown', 'Chocolate Brown', 'Coffee Brown', 'Tan', 'Taupe', 'Chestnut', 'Cinnamon', 'Khaki', 'Mahogany', 'Walnut', 'Sienna', 'Burgundy', 'Coral', 'Magenta'],
            ['Fall', 'Spring', 'Summer', 'Winter'],
            ['Casual', 'Ethnic', 'Formal', 'Party', 'Smart Casual', 'Sports', 'Travel']]

bottom_list = [['Capris', 'Churidar', 'Jeans', 'Jeggings', 'Leggings', 'Patiala', 'Salwar', 'Salwar and Dupatta', 'Shorts', 'Skirts', 'Stockings', 'Swimwear', 'Tights', 'Track Pants', 'Tracksuits', 'Trousers'],
               ['Boys', 'Girls', 'Men', 'Unisex', 'Women'],
               ['Black', 'Blue', 'Navy Blue', 'Sky Blue', 'Dark Blue', 'Light Blue', 'Dark Green', 'Olive Green', 'Light Green', 'Dark Yellow', 'Light Yellow', 'Green', 'Grey', 'Light Grey', 'Dark Grey', 'Multi', 'Orange', 'Dark Orange', 'Peach', 'Pink', 'Hot Pink', 'Purple', 'Lavender', 'Red', 'Maroon', 'White', 'Off White', 'Yellow', 'Beige', 'Brown', 'Dark Brown', 'Light Brown', 'Chocolate Brown', 'Coffee Brown', 'Tan', 'Taupe', 'Chestnut', 'Cinnamon', 'Khaki', 'Mahogany', 'Walnut', 'Sienna', 'Burgundy', 'Coral', 'Magenta'],
               ['Fall', 'Spring', 'Summer', 'Winter'],
               ['Casual', 'Ethnic', 'Formal', 'Smart Casual', 'Sports']]

foot_list = [['Casual Shoes', 'Flats', 'Flip Flops', 'Formal Shoes', 'Heels', 'Sandals', 'Sports Sandals', 'Sports Shoes'],
             ['Boys', 'Girls', 'Men', 'Unisex', 'Women'],
             ['Black', 'Blue', 'Navy Blue', 'Sky Blue', 'Dark Blue', 'Light Blue', 'Dark Green', 'Olive Green', 'Light Green', 'Dark Yellow', 'Light Yellow', 'Green', 'Grey', 'Light Grey', 'Dark Grey', 'Multi', 'Orange', 'Dark Orange', 'Peach', 'Pink', 'Hot Pink', 'Purple', 'Lavender', 'Red', 'Maroon', 'White', 'Off White', 'Yellow', 'Beige', 'Brown', 'Dark Brown', 'Light Brown', 'Chocolate Brown', 'Coffee Brown', 'Tan', 'Taupe', 'Chestnut', 'Cinnamon', 'Khaki', 'Mahogany', 'Walnut', 'Sienna', 'Burgundy', 'Coral', 'Magenta'],
             ['Fall', 'Spring', 'Summer', 'Winter'],
             ['Casual', 'Ethnic', 'Formal', 'Party', 'Smart Casual', 'Sports']]

def convert_rgb_to_names(rgb_tuple):
    css3_db = CSS3_HEX_TO_NAMES
    rgb_values = []
    names = []
    for color_hex, color_name in css3_db.items():
        if len(color_hex) == 7:
            #rgb_values.append(rgb_tuple)
            names.append(color_name)
            rgb_values.append(hex_to_rgb(color_hex))

    kdt_db = KDTree(rgb_values)
    distance, index = kdt_db.query(rgb_tuple)
    return  names[index]
def get_dominant_color(image, k=6, ignore_white=True):
    image = image.resize((60, 80))
    image_np = np.array(image)
    pixels = image_np.reshape((-1, 3))
    kmeans = KMeans(n_clusters=k, random_state=0, n_init=10).fit(pixels)
    counts = np.bincount(kmeans.labels_)
    cluster_centers = kmeans.cluster_centers_
    sorted_indices = np.argsort(-counts)
    total_count = np.sum(counts)

    for idx in sorted_indices:
        dominant_color = tuple(map(int, cluster_centers[idx]))
        if counts[idx] / total_count < 0.05:
            continue
        if ignore_white:
            hsv = colorsys.rgb_to_hsv(*[x / 255.0 for x in dominant_color])
            if hsv[1] < 0.1 and hsv[2] > 0.9:
                continue
        return dominant_color

    return (0, 0, 0)

def color_classification(image):
    dominant_color = get_dominant_color(image)
    print(f"Dominant Color: {dominant_color}")
    color_name = convert_rgb_to_names(dominant_color)
    print(f"Color Name: {color_name}")
    return color_name

def single_helper(train_images, model, lelist):
    my_predictions = model.predict(train_images)
    result = []
    for i in range(len(lelist)):
        type_predicted_label = np.argmax(my_predictions[i][0])
        result.append(lelist[i][type_predicted_label])
    return result

def image_classification(image_data, url):
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

        pil_image = Image.fromarray(cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB))
        color = color_classification(pil_image)
        result.append(url)
        result_str = [result[0], result[1], color, result[2], result[3], result[4], url]
        return category, result_str, result

    except Exception as e:
        print("Error in image_classification:", e)
        traceback.print_exc()
        return None

def find_combo_by_top(top_color_group, combotype):
    co = int(combotype / 30)
    if top_color_group in [14, 15]:
        bottom_color_group = random.choice([12, 13, 14])
        shoes_color_group = 13 if bottom_color_group == 12 else random.choice([12, 13])
    elif top_color_group in [12, 13]:
        bottom_color_group = random.choice([12, 13])
        shoes_color_group = 13 if bottom_color_group == 12 else random.choice([12, 13])
    else:
        bottom_color_group = random.choice([max(top_color_group - co, 0), min(top_color_group + co, 15)])
        shoes_color_group = (top_color_group + co) % 16 if bottom_color_group == max(top_color_group - co, 0) else max(top_color_group - co, 0)

    return bottom_color_group, shoes_color_group

def create_color_group_mapping(css3_hex_to_names):
    """
    Creates a mapping of color names to their respective color group identifiers based on predefined mapping.
    
    Args:
        css3_hex_to_names (dict): A dictionary mapping CSS3 color hex values to color names.
    
    Returns:
        dict: A dictionary mapping color names to their corresponding color group identifiers.
    """
    predefined_mapping = {
        'Black': 12, 'White': 13, 'Grey': 14, 'Multi': 15, 'Dark Blue': 0, 'Blue': 1, 'Light Blue': 2,
        'Dark Green': 3, 'Green': 4, 'Dark Yellow': 5, 'Yellow': 6, 'Orange': 7, 'Pink': 8, 'Purple': 9,
        'Red': 10, 'Dark Orange': 11
    }
    
    color_groups = {
        'Black': ['Black', 'DimGray', 'Gray', 'DarkGray', 'Silver', 'LightGray', 'Gainsboro', 'WhiteSmoke', 'White'],
        'White': ['Snow', 'HoneyDew', 'MintCream', 'Azure', 'AliceBlue', 'GhostWhite', 'WhiteSmoke', 'SeaShell', 'Beige', 'OldLace', 'FloralWhite', 'Ivory', 'AntiqueWhite', 'Linen', 'LavenderBlush', 'MistyRose'],
        'Grey': ['DarkSlateGray', 'SlateGray', 'LightSlateGray', 'Gray', 'DimGray'],
        'Multi': ['Multi'],
        'Dark Blue': ['Navy', 'DarkBlue', 'MediumBlue', 'Blue', 'MidnightBlue', 'RoyalBlue', 'SteelBlue', 'DodgerBlue', 'DeepSkyBlue', 'CornflowerBlue', 'SkyBlue', 'LightSkyBlue', 'LightSteelBlue', 'LightBlue', 'PowderBlue'],
        'Blue': ['Blue', 'MediumBlue', 'LightBlue', 'PowderBlue'],
        'Light Blue': ['LightBlue', 'PowderBlue'],
        'Dark Green': ['DarkGreen', 'Green', 'ForestGreen', 'SeaGreen', 'DarkOliveGreen', 'Olive', 'OliveDrab', 'DarkSeaGreen', 'LightSeaGreen', 'MediumSeaGreen', 'SpringGreen', 'MediumSpringGreen', 'LightGreen', 'PaleGreen'],
        'Green': ['Green', 'LightGreen', 'PaleGreen'],
        'Dark Yellow': ['Gold', 'Yellow', 'LightYellow', 'LemonChiffon', 'LightGoldenRodYellow', 'PapayaWhip', 'Moccasin', 'PeachPuff', 'PaleGoldenRod', 'Khaki', 'DarkKhaki'],
        'Yellow': ['Yellow', 'LightYellow'],
        'Orange': ['Orange', 'DarkOrange', 'Coral', 'LightCoral', 'Tomato', 'OrangeRed', 'Red', 'HotPink', 'DeepPink', 'Pink', 'LightPink'],
        'Pink': ['Pink', 'LightPink', 'HotPink', 'DeepPink'],
        'Purple': ['Lavender', 'Thistle', 'Plum', 'Violet', 'Orchid', 'Fuchsia', 'Magenta', 'MediumOrchid', 'MediumPurple', 'BlueViolet', 'DarkViolet', 'DarkOrchid', 'DarkMagenta', 'Purple', 'Indigo'],
        'Red': ['Red', 'DarkRed', 'Maroon', 'FireBrick', 'Crimson', 'IndianRed', 'LightCoral', 'Salmon', 'DarkSalmon', 'LightSalmon'],
        'Dark Orange': ['DarkOrange', 'OrangeRed']
    }
    
    color_group_mapping = {}
    for group, colors in color_groups.items():
        for color in colors:
            color_group_mapping[color] = predefined_mapping[group]
    
    return color_group_mapping
