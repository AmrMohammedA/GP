from wsgiref.util import request_uri
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
import flask
import requests
from werkzeug.utils import secure_filename
from outfit_generator import single_classification
import numpy as np
import os
from datetime import date

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory(path,'static')

SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'

swaggerui_blueprint =get_swaggerui_blueprint(
    SWAGGER_URL, 
    API_URL,
    config={
        'app_name': "Seans-Python-Flask-REST-Boilerplate"
    }
)

app.register_blueprint(swaggerui_blueprint ,url_prefix=SWAGGER_URL)
#app.register_blueprint(request_api.get_blueprint())

class OutfitGenerator:
    def __init__(self):
        self.top = []
        self.bottom = []
        self.shoes = []

    def add_top(self, photo_path, output_data):
        self.top.append((photo_path, output_data))

    def add_bottom(self, photo_path, output_data):
        self.bottom.append((photo_path, output_data))

    def add_shoes(self, photo_path, output_data):
        self.shoes.append((photo_path, output_data))

    def print_outfit_data(self):
        print("Tops:")
        for top_item in self.top:
            print("Photo Path:", top_item[0])
            print("Output Data:", top_item[1])
            print()

        print("Bottoms:")
        for bottom_item in self.bottom:
            print("Photo Path:", bottom_item[0])
            print("Output Data:", bottom_item[1])
            print()

        print("Shoes:")
        for shoes_item in self.shoes:
            print("Photo Path:", shoes_item[0])
            print("Output Data:", shoes_item[1])
            print()


outfit_generator = OutfitGenerator()
# Printing the outfit data


@app.route('/')
def index():
    return render_template('indexx.html')


import requests
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}
@app.route('/add_photo', methods=['POST'])
@app.route('/add_photo', methods=['POST'])
def add_photo():
    try:
        # Check if the request contains a URL parameter
        if 'url' not in request.form:
            return jsonify({'success': False, 'message': 'No URL provided'})

        # Extract the URL from the request
        url = request.form['url']

        # Download the image from the URL
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({'success': False, 'message': 'Failed to download image from URL'})

        # Save the image to a temporary file
        temp_filename = 'temp_image.jpg'
        with open(temp_filename, 'wb') as f:
            f.write(response.content)

        # Process the image using single_classification function
        sub, info, res_place_holder = single_classification(temp_filename)

        # Add the processed image data to the appropriate list
        if sub == "top":
            outfit_generator.top.append((info, res_place_holder))
        elif sub == "bottom":
            outfit_generator.bottom.append((info, res_place_holder))
        elif sub == "foot":
            outfit_generator.shoes.append((info, res_place_holder))
        json_data = {
                    'Photo Path': info,
                    'Output Data': res_place_holder
                }
        # Send a POST request to the backend endpoint
        response =jsonify(json_data)
        # Check if the request was successful
        if response.status_code == 200:
            return jsonify(json_data)
        else:
            return jsonify({'success': False, 'message': 'Failed to add photo to backend'})
        # Delete the temporary file
        os.remove(temp_filename)

        return jsonify({'success': True, 'message': 'Image added successfully'})
    except Exception as e:
        print("Error in add_photo:", e)
        return jsonify({'success': False, 'message': 'Internal server error'})
'''@app.route('/generate_outfit', methods=['POST'])
def generate_outfit( ):
    try:
        toseason = request.json.post('toseason', '')  # Extracting toseason from JSON data    # as a client 
        #toseason = request.json.get('toseason', '')  # Extracting toseason from JSON data    # as a server 
        # Send a POST request to the endpoint that provides the outfit data
        
        # Send a POST request to the endpoint that provides the outfit data
        response = requests.post('http://127.0.0.1:5000/get_outfit_data', json={'toseason': toseason})
        data = response.json()

        # Extract the lists from the response data
        top = data.post('top', [])
        bottom = data.post('bottom', [])
        shoes = data.post('shoes', [])
        if top:
            print("Top list appended successfully:", top)
        if bottom:
            print("Bottom list appended successfully:", bottom)
        if shoes:
            print("Shoes list appended successfully:", shoes)

        todays_date = date.today()
        tomonth = todays_date.month
        if tomonth in [3, 4, 5]:
            toseason = "Spring"
        elif tomonth in [6, 7, 8]:
            toseason = "Summer"
        elif tomonth in [9, 10, 11]:
            toseason = "Fall"
        else:
            toseason = "Winter"

        # تحويل القوائم المتعددة الأبعاد إلى قوائم واحدة الأبعاد
        flattened_top = [item for sublist in top for item in sublist]
        flattened_bottom = [item for sublist in bottom for item in sublist]
        flattened_shoes = [item for sublist in shoes for item in sublist]

        top_right_season = [i for i in flattened_top if i[3] == toseason]
        ad_top = np.random.choice(top_right_season) if top_right_season else None

        if ad_top is None:
            return jsonify({'success': False, 'message': 'No outfit available for the specified season'})

        helper_bot = [i for i in flattened_bottom if i[4] == ad_top[4]]
        helper_sho = [i for i in flattened_shoes if i[4] == ad_top[4]]

        ad_bot = None
        if helper_bot:
            bot_right_season = [i for i in helper_bot if i[3] == toseason]
            ad_bot = np.random.choice(bot_right_season) if bot_right_season else None
        if ad_bot is None:
            ad_bot = np.random.choice(flattened_bottom)

        ad_sho = None
        if helper_sho:
            sho_right_season = [i for i in helper_sho if i[3] == toseason]
            ad_sho = np.random.choice(sho_right_season) if sho_right_season else None
        if ad_sho is None:
            ad_sho = np.random.choice(flattened_shoes)
        

        generated_outfit = {'top': ad_top[-1], 'bottom': ad_bot[-1], 'shoes': ad_sho[-1]}
        return jsonify({'success': True, 'generated_outfit': generated_outfit})
    except Exception as e:
        print("Error in generate_outfit:", e)
        return jsonify({'success': False, 'message': 'Failed to generate outfit recommendation'})


'''
@app.route('/generate_outfit', methods=['POST'])
def generate_outfit():
    try:
        data = request.json
        
        toseason = data.get('toseason', '')

        top = data.get('top', [])
        bottom = data.get('bottom', [])
        shoes = data.get('shoes', [])

        flattened_top = [item['Output Data'] for item in top]
        flattened_bottom = [item['Output Data'] for item in bottom]
        flattened_shoes = [item['Output Data'] for item in shoes]

        # Logic to determine the season if not provided
        if not toseason:
            todays_date = date.today()
            tomonth = todays_date.month
            if tomonth in [3, 4, 5]:
                toseason = "Spring"
            elif tomonth in [6, 7, 8]:
                toseason = "Summer"
            elif tomonth in [9, 10, 11]:
                toseason = "Fall"
            else:
                toseason = "Winter"
                
        top_right_season = [i for i in flattened_top if i[3] == toseason]
        print("top_right_season:", top_right_season)

        ad_top = np.random.choice(top_right_season) if top_right_season else None
        print("ad_top:", ad_top)

        if ad_top is None:
            return jsonify({'success': False, 'message': 'No outfit available for the specified season'})

        helper_bot = [i for i in flattened_bottom if i[4] == ad_top[4]]
        print("helper_bot:", helper_bot)

        helper_sho = [i for i in flattened_shoes if i[4] == ad_top[4]]
        print("helper_sho:", helper_sho)

        ad_bot = None
        if helper_bot:
            bot_right_season = [i for i in flattened_bottom if i[3] == toseason]
            print("bot_right_season:", bot_right_season)
            ad_bot = np.random.choice(bot_right_season) if bot_right_season else None
            print("ad_bot:", ad_bot)
        if ad_bot is None:
            ad_bot = np.random.choice(flattened_bottom)
            print("ad_bot (default):", ad_bot)

        ad_sho = None
        if helper_sho:
            sho_right_season = [i for i in flattened_shoes if i[3] == toseason]
            print("sho_right_season:", sho_right_season)
            ad_sho = np.random.choice(sho_right_season) if sho_right_season else None
            print("ad_sho:", ad_sho)
        if ad_sho is None:
            ad_sho = np.random.choice(flattened_shoes)
            print("ad_sho (default):", ad_sho)

        generated_outfit = {'top': ad_top, 'bottom': ad_bot, 'shoes': ad_sho}
        return jsonify({'success': True, 'generated_outfit': generated_outfit})
    except Exception as e:
        print("Error in generate_outfit:", e)
        return jsonify({'success': False, 'message': 'Failed to generate outfit recommendation'})



'''@app.route('/get_outfit_data', methods=['POST'])
def get_outfit_data():
    try:
        data = request.get_json()
        top = data.get('top', [])
        bottom = data.get('bottom', [])
        shoes = data.get('shoes', [])

        top_data = [{'photo_path': item[0], 'output_data': item[1]} for item in top]
        bottom_data = [{'photo_path': item[0], 'output_data': item[1]} for item in bottom]
        shoes_data = [{'photo_path': item[0], 'output_data': item[1]} for item in shoes]

        outfit_data = {
            'top': top_data,
            'bottom': bottom_data,
            'shoes': shoes_data
        }
        
        return jsonify({'success': True, 'outfit_data': outfit_data})#<========================================================look here
    except Exception as e:
        print("Error in get_outfit_data:", e)
        return jsonify({'success': False, 'message': 'Failed to retrieve outfit data'})

'''


if __name__ == '__main__':
    app.run(debug=False)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


if __name__ == '__main__':
    app.run(debug=False)
