from flask import Blueprint, render_template, send_from_directory
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image  # Import PIL for image conversion

# Create blueprint
bp = Blueprint("his", __name__, url_prefix="/his")

# Define the paths to the uploads and results folders
UPLOAD_FOLDER = 'uploads'  # uploads folder is in the project root
RESULTS_FOLDER = os.path.join('static', 'results')  # results folder is in static/results
CONVERTED_UPLOADS_FOLDER = os.path.join('static', 'converted_uploads')  # Folder for converted PNGs

# Ensure the converted uploads directory exists
if not os.path.exists(CONVERTED_UPLOADS_FOLDER):
    os.makedirs(CONVERTED_UPLOADS_FOLDER)

def get_recent_uploads(num_files=3):
    """Get the most recent upload images and convert them to PNG."""
    # Get all image files from the uploads folder
    upload_files = os.listdir(UPLOAD_FOLDER)
    upload_image_files = [
        f for f in upload_files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif'))
    ]
    # Sort upload images by datetime
    def extract_datetime(filename):
        # Assuming filename format: YYYYMMDD_HHMMSS_other_info.ext
        parts = filename.split('_')
        if len(parts) >= 2:
            date_str = parts[0]
            time_str = parts[1]
            try:
                return datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
            except ValueError:
                pass
        return datetime.min  # If unable to parse, return minimal datetime

    upload_image_files.sort(key=extract_datetime, reverse=True)
    recent_upload_files = upload_image_files[:num_files]  # Get the latest upload images

    converted_images = []

    for upload_file in recent_upload_files:
        # Extract date information
        parts = upload_file.split('_')
        date_str = parts[0]
        time_str = parts[1] if len(parts) > 1 else '000000'
        try:
            date_time = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
            date_formatted = date_time.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            date_formatted = 'Unknown Date'

        # Convert upload image to PNG before referencing
        # Get the base filename without extension
        base_filename = os.path.splitext(upload_file)[0]
        converted_filename = base_filename + '.png'
        converted_filepath = os.path.join(CONVERTED_UPLOADS_FOLDER, converted_filename)

        # Check if converted file exists
        if not os.path.exists(converted_filepath):
            # Open the image and convert to PNG
            original_filepath = os.path.join(UPLOAD_FOLDER, upload_file)
            try:
                with Image.open(original_filepath) as img:
                    # Convert image to RGB mode if necessary
                    if img.mode in ("RGBA", "P", "L"):
                        img = img.convert("RGB")
                    img.save(converted_filepath, 'PNG')
            except Exception as e:
                print(f"Error converting image {upload_file}: {e}")
                # Use a placeholder image or skip
                converted_filename = 'placeholder.png'  # Ensure this exists in static/converted_uploads

        converted_images.append({
            'date': date_formatted,
            'model': 'U-net',  # Add model info if available
            'query_image': converted_filename,  # Use the converted PNG filename
            'original_filename': upload_file  # Store the original filename for mapping
        })

    return converted_images

def get_recent_results(num_files=3):
    """Get the most recent result images."""
    # Get all image files from the results folder
    result_files = os.listdir(RESULTS_FOLDER)
    result_image_files = [
        f for f in result_files if f.lower().endswith('.png')  # Only PNGs in results
    ]
    # Sort result images by datetime
    def extract_result_datetime(filename):
        # Assuming filename format: result_YYYYMMDD_HHMMSS_other_info.png
        parts = filename.split('_')
        if len(parts) >= 3:
            date_str = parts[1]
            time_str = parts[2]
            try:
                return datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
            except ValueError:
                pass
        return datetime.min  # If unable to parse, return minimal datetime

    result_image_files.sort(key=extract_result_datetime, reverse=True)
    recent_result_files = result_image_files[:num_files]  # Get the latest result images

    result_images = {}

    for result_file in recent_result_files:
        # Remove 'result_' prefix and extension to get the identifier
        identifier_with_ext = result_file[len('result_'):]
        identifier = os.path.splitext(identifier_with_ext)[0]
        result_images[identifier] = result_file

    return result_images

@bp.route('/history', methods=['GET'])
def history():
    """Render the prediction history page."""
    # Get recent uploads and results
    recent_uploads = get_recent_uploads(num_files=4)
    recent_results = get_recent_results(num_files=4)

    prediction_history = []

    for upload in recent_uploads:
        # Use original upload filename (without extension) to find corresponding result
        identifier = os.path.splitext(upload['original_filename'])[0]
        result_file = recent_results.get(identifier, None)
        if not result_file:
            # If not found, use placeholder
            result_file = 'result_placeholder.png'  # Ensure this exists in static/results

        # Append to prediction history
        prediction_history.append({
            'date': upload['date'],
            'model': upload['model'],
            'query_image': upload['query_image'],  # Converted PNG filename
            'result_image': result_file
        })

    return render_template('history.html', prediction_history=prediction_history)
