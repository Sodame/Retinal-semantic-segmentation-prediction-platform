from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import zipfile
import os
from datetime import datetime
import torch
from Unet_Model import AggreUNet, Unet_evaluate_single_image, Unet_save_pred_mask, Unet_save_pred_mask1, compute_metrics
from flask_migrate import Migrate
from exts import db, mail
import config
from blueprints.auth import bp as auth_bp
from blueprints.qa import bp as qa_bp
from blueprints.his import bp as his_bp
from flask import session
from databaseModel import UserModel, History
import requests
from PIL import Image
from torchvision import transforms
import io

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'static/results'
LABEL_FOLDER = 'labels'
PROCESSED_ZIP_FOLDER = 'processed_zips'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['LABEL_FOLDER'] = LABEL_FOLDER
app.config['PROCESSED_ZIP_FOLDER'] = PROCESSED_ZIP_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
os.makedirs(LABEL_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_ZIP_FOLDER, exist_ok=True)

mask_transform = transforms.Compose([
    transforms.Resize((512, 512), interpolation=Image.NEAREST),
    transforms.ToTensor()
])

def process_docker_returned_image(response_content,device):
    # Load the returned PNG image as a PIL Image
    result_img = Image.open(io.BytesIO(response_content)).convert("L")  # Convert to single channel grayscale image

    mask_tensor = mask_transform(result_img).unsqueeze(0).to(device)

    return mask_tensor

def load_ground_truth_mask(image_filename, label_folder='labels'):
    # Extract file name prefix
    prefix = image_filename.split('_')[0]
    mask_filename = f"{prefix}_manual1.gif"
    mask_path = os.path.join(label_folder, mask_filename)

    if os.path.exists(mask_path):
        # Load the label image and apply the transformation
        mask = Image.open(mask_path).convert('L')  #
        mask = mask_transform(mask).unsqueeze(0).to(device)  # shift to GPU/CPU
        return mask
    else:
        raise FileNotFoundError(f"The corresponding tag file could not be found：{mask_path}")


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

app.config.from_object(config)

db.init_app(app)
mail.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(auth_bp)
app.register_blueprint(qa_bp)
app.register_blueprint(his_bp)
DOCKER_URL = "http://host.docker.internal:5001/predict"

def call_docker_model(file_path):
    """Call the VesselSeg model in the Docker container for inference"""
    with open(file_path, 'rb') as img_file:
        files = {'file': img_file}
        response = requests.post(DOCKER_URL, files=files)
        if response.status_code == 200:
            # Save the returned result image
            result_filename = f"result_{os.path.basename(file_path)}"
            result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)
            with open(result_path, 'wb') as f:
                f.write(response.content)
            return result_path
        else:
            raise ValueError(f"Failed to get prediction from Docker: {response.text}")

def call_docker_prediction(file_path,device):
    """Call the model in the Docker container for inference and return the resulting image data"""
    with open(file_path, 'rb') as img_file:
        files = {'file': img_file}
        response = requests.post(DOCKER_URL, files=files)
        if response.status_code == 200:
            processed_mask = process_docker_returned_image(response.content,device=device)
            return processed_mask
        else:
            raise ValueError(f"Failed to get prediction from Docker: {response.text}")

# Load models
def load_model(model_type):
    if model_type == 'unet':
        model = AggreUNet(n_class=1).to(device)
        model.load_state_dict(torch.load('modelWeight/aggreunet_model.pth', map_location=device))
    elif model_type == 'laddernet':
        model = AggreUNet(n_class=1).to(device)
        model.load_state_dict(torch.load('modelWeight/aggreunet_model.pth', map_location=device))
    else:
        raise ValueError("Invalid model type selected.")

    model.eval()
    return model


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    user = UserModel.query.get(user_id)

    if 'file' not in request.files:
        return 'No file part'

    file = request.files['file']
    model_type = request.form.get('model')

    if file.filename == '':
        return 'No selected file'

    try:
        model = load_model(model_type)
        if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tif')):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            if model_type == 'unet':
                pred_mask = Unet_evaluate_single_image(model, file_path, device)
                result_path = Unet_save_pred_mask(pred_mask, filename)
            elif model_type == 'laddernet':
                pred_mask = call_docker_prediction(file_path,device)
                result_path = call_docker_model(file_path)
            else:
                return 'Invalid model type selected'
            result_filename = os.path.basename(result_path)
            new_history = History(
                filename=filename,
                result_filename=result_filename,
                model=model_type,
                user_id=user.id,
                timestamp=datetime.utcnow()
            )
            db.session.add(new_history)
            db.session.commit()

            ground_truth_mask = load_ground_truth_mask(file.filename, label_folder=app.config['LABEL_FOLDER'])
            dice, iou, accuracy, recall, f1_score = compute_metrics(pred_mask, ground_truth_mask)
            return render_template(
                'result.html',
                result_image=os.path.basename(result_path),
                test_dice=dice,
                test_iou=iou,
                test_accuracy=accuracy,
                test_recall=recall,
                test_f1_score=f1_score
            )


        elif file and file.filename.endswith('.zip'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"{timestamp}_{file.filename}"
            zip_file_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
            file.save(zip_file_path)

            temp_extract_folder = os.path.join(app.config['UPLOAD_FOLDER'], timestamp)
            os.makedirs(temp_extract_folder, exist_ok=True)
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_folder)
            processed_files = []
            temp_folder = os.path.join(app.config['RESULT_FOLDER'], timestamp)
            os.makedirs(temp_folder, exist_ok=True)

            total_dice, total_iou, total_accuracy, total_recall, total_f1_score = 0, 0, 0, 0, 0
            num_images = 0

            for img_file in os.listdir(temp_extract_folder):
                if img_file.lower().endswith(('.png', '.jpg', '.jpeg', '.tif')):
                    img_path = os.path.join(temp_extract_folder, img_file)
                    if model_type == 'unet':
                        pred_mask = Unet_evaluate_single_image(model, img_path, device)
                        result_path = Unet_save_pred_mask1(pred_mask, img_file, temp_folder)
                    elif model_type == 'laddernet':
                        pred_mask = call_docker_prediction(img_path, device)
                        result_path = call_docker_model(img_path)
                    else:
                        return 'Invalid model type selected'

                    ground_truth_mask = load_ground_truth_mask(img_file, label_folder=app.config['LABEL_FOLDER'])
                    dice, iou, accuracy, recall, f1_score = compute_metrics(pred_mask, ground_truth_mask)
                    total_dice += dice
                    total_iou += iou
                    total_accuracy += accuracy
                    total_recall += recall
                    total_f1_score += f1_score
                    num_images += 1

                    result_filename = os.path.basename(result_path)
                    processed_files.append(result_path)
                    new_history = History(
                        filename=img_file,
                        result_filename=result_filename,
                        model=model_type,
                        user_id=user.id,
                        timestamp=datetime.utcnow()
                    )
                    db.session.add(new_history)
            db.session.commit()

            # Calculate average index
            avg_dice = total_dice / num_images
            avg_iou = total_iou / num_images
            avg_accuracy = total_accuracy / num_images
            avg_recall = total_recall / num_images
            avg_f1_score = total_f1_score / num_images

            processed_zip_filename = f"{timestamp}_processed.zip"
            processed_zip_path = os.path.join(app.config['PROCESSED_ZIP_FOLDER'], processed_zip_filename)
            with zipfile.ZipFile(processed_zip_path, 'w') as zipf:
                for file in processed_files:
                    zipf.write(file, os.path.basename(file))

            return render_template('result.html', result_zip=processed_zip_filename, images=processed_files, test_dice=avg_dice, test_iou=avg_iou, test_accuracy=avg_accuracy, test_recall=avg_recall,test_f1_score=avg_f1_score)
    except Exception as e:
        return f"An error occurred during the process: {str(e)}"

    return 'Please upload a valid image file or ZIP file containing images.'


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Provide the processed ZIP file for user download."""
    return send_from_directory(app.config['PROCESSED_ZIP_FOLDER'], filename, as_attachment=True)


# Run the app
if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)