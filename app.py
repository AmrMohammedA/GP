import numpy as np
import os
import json
from flask import request, Flask, render_template, jsonify, send_from_directory
import requests
import cv2
from outfit_generator import *
from datetime import date, datetime  
from colors import CSS3_HEX_TO_NAMES  # Import the color definitions from colors.py
from keras.models import load_model
from PIL import Image
from scipy.spatial import KDTree
from webcolors import hex_to_rgb
from sklearn.cluster import KMeans
import colorsys
import random
import traceback

app = Flask(__name__)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

class OutfitGenerator:
    def __init__(self):
        self.top = []
        self.bottom = []
        self.shoes = []

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/')
def index():
    return render_template('indexx.html')

@app.route('/add_photo', methods=['POST'])
def add_photo():
    try:
        image_url = request.json.get('url')
        if not image_url:
            return jsonify({'success': False, 'message': 'No URL provided'})
        
        response = requests.get(image_url)
        if response.status_code != 200:
            return jsonify({'success': False, 'message': 'Failed to fetch image from URL'})
        
        image_data = np.asarray(bytearray(response.content), dtype=np.uint8)
        img = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'success': False, 'message': 'Failed to decode image'})
        
        sub, info, res_place_holder = image_classification(img, image_url)
        if res_place_holder is None:
            return jsonify({'success': False, 'message': 'Error in single classification'})
        
        response_data = {
            'success': True,
            'message': 'Photo processed successfully',
            'Photo Path': info,
            'Output Data': res_place_holder,
            'List Type': sub,
        }
        return jsonify(response_data)
    except Exception as e:
        print("Error in add_photo:", e)
        return jsonify({'success': False, 'message': 'Internal server error'})

def get_season():
    todays_date = date.today()
    tomonth = todays_date.month
    if tomonth in [3, 4, 5]:
        return "Spring"
    elif tomonth in [6, 7, 8]:
        return "Summer"
    elif tomonth in [9, 10, 11]:
        return "Fall"
    else:
        return "Winter"

@app.route('/receive_and_generate', methods=['POST'])
def receive_and_generate():
    try:
        current_season = get_season()
        data = request.json

        if 'data' not in data:
            return jsonify({'success': False, 'message': 'No data found'}), 400

        outfit_generator = OutfitGenerator()

        for item in data["data"]:
            photo_path = item.get("photoPath", [])
            output_data = item.get("outputData", [])
            
            list_type = item.get("listType")
            if list_type == "top":
                outfit_generator.top.append((photo_path, output_data))
            elif list_type == "bottom":
                outfit_generator.bottom.append((photo_path, output_data))
            elif list_type == "foot":
                outfit_generator.shoes.append((photo_path, output_data))
            else:
                return jsonify({'success': False, 'message': f'Invalid listType: {list_type}'}), 400

        top_right_season = [i for i in outfit_generator.top if i[1][3] == current_season]
        ad_top = random.choice(top_right_season) if top_right_season else random.choice(outfit_generator.top)

        top_color = ad_top[1][2]
        color_group_mapping = {
            'Black': 12, 'White': 13, 'Grey': 14, 'Multi': 15, 'Dark Blue': 0, 'Blue': 1, 'Light Blue': 2,
            'Dark Green': 3, 'Green': 4, 'Dark Yellow': 5, 'Yellow': 6, 'Orange': 7, 'Pink': 8, 'Purple': 9,
            'Red': 10, 'Dark Orange': 11
        }
        top_color_group = color_group_mapping.get(top_color, -1)
        if top_color_group == -1:
            return jsonify({'success': False, 'message': 'Invalid top color'}), 400

        bottom_color_group, shoes_color_group = find_combo_by_top(top_color_group, 30)

        bottom_right_season = [i for i in outfit_generator.bottom if i[1][3] == current_season and color_group_mapping.get(i[1][2], -1) == bottom_color_group]
        shoes_right_season = [i for i in outfit_generator.shoes if i[1][3] == current_season and color_group_mapping.get(i[1][2], -1) == shoes_color_group]

        ad_bot = random.choice(bottom_right_season) if bottom_right_season else random.choice(outfit_generator.bottom)
        ad_sho = random.choice(shoes_right_season) if shoes_right_season else random.choice(outfit_generator.shoes)

        response = {
            'top': ad_top[0],
            'bottom': ad_bot[0],
            'shoes': ad_sho[0]
        }

        return jsonify(response), 200
    except Exception as e:
        print("Error in receive_and_generate:", e)
        return jsonify({'message': 'Failed to process data and generate outfit'}), 500

if __name__ == '__main__':
    app.run(debug=False)
    app.run(host='0.0.0.0', port=5000)
