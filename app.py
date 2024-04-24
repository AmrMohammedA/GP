from flask import Flask, render_template, request, jsonify
import flask
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


class OutfitGenerator:
    def __init__(self):
        self.top = []
        self.bottom = []
        self.shoes = []


outfit_generator = OutfitGenerator()


def generate_outfit_recommendation(top, bottom, shoes, toseason):
    # تحويل القوائم المتعددة الأبعاد إلى قوائم واحدة الأبعاد
    flattened_top = [item for sublist in top for item in sublist]
    flattened_bottom = [item for sublist in bottom for item in sublist]
    flattened_shoes = [item for sublist in shoes for item in sublist]

    top_right_season = [i for i in flattened_top if i[3] == toseason]
    ad_top = np.random.choice(top_right_season) if top_right_season else None

    if ad_top is None:
        return "DefaultTop", "DefaultBottom", "DefaultShoes"

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

    return ad_top[-1], ad_bot[-1], ad_sho[-1]


@app.route('/')
def index():
    return render_template('indexx.html')


@app.route('/add_photo', methods=['POST'])
def add_photo():
    try:
        if 'directory' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'})

        file = request.files['directory']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'})

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            try:
                sub, info, res_place_holder = single_classification(file_path)

                if sub == "top":
                    outfit_generator.top.append((info, res_place_holder))
                elif sub == "bottom":
                    outfit_generator.bottom.append((info, res_place_holder))
                elif sub == "foot":
                    outfit_generator.shoes.append((info, res_place_holder))

                return jsonify({'success': True, 'message': 'Photo added successfully'})
            except Exception as e:
                print("Error in single_classification:", e)
                return jsonify({'success': False, 'message': 'Error in single_classification'})
        else:
            return jsonify({'success': False, 'message': 'Invalid file type'})
    except Exception as e:
        print("Error in add_photo:", e)
        return jsonify({'success': False, 'message': 'Internal server error'})


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


@app.route('/generate_outfit', methods=['GET'])
def generate_outfit():
    try:
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

        ad_top_path, ad_bot_path, ad_sho_path = generate_outfit_recommendation(
            [item[1] for item in outfit_generator.top],
            [item[1] for item in outfit_generator.bottom],
            [item[1] for item in outfit_generator.shoes],
            toseason
        )

        if ad_top_path is None or ad_bot_path is None or ad_sho_path is None:
            return render_template('indexx.html', message="No outfit available for the specified season")

        generated_outfit = {'top': ad_top_path, 'bottom': ad_bot_path, 'shoes': ad_sho_path}
        return render_template('indexx.html', generated_outfit=generated_outfit)
    except Exception as e:
        print("Error in generate_outfit:", e)
        return render_template('indexx.html', message="Failed to generate outfit recommendation")
print(flask.__version__)

if __name__ == '__main__':
    app.run(debug=False)
