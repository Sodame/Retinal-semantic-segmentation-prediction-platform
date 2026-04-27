import os
import io
import torch
import numpy as np
from PIL import Image
from flask import Flask, request, send_file, jsonify
from models import LadderNet
from lib.common import setpu_seed

setpu_seed(2024)

app = Flask(__name__)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
net = LadderNet(inplanes=1, num_classes=2, layers=3, filters=16).to(device)
net.eval()

checkpoint_path = os.path.join("experiments", "UNet_vessel_seg", "best_model.pth")
checkpoint = torch.load(checkpoint_path, map_location=device)
net.load_state_dict(checkpoint['net'])

def preprocess_image(image):
    img = image.convert('L').resize((576, 576))
    img = np.array(img)[np.newaxis, np.newaxis, ...] / 255.0
    return torch.tensor(img, dtype=torch.float32).to(device)

def postprocess_output(output, threshold=0.3):
    binary_img = (output[0] > threshold).astype(np.uint8) * 255
    binary_img = Image.fromarray(binary_img.squeeze())
    return binary_img

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    img = Image.open(io.BytesIO(file.read()))
    input_tensor = preprocess_image(img)
    with torch.no_grad():
        output = net(input_tensor)
        output = output[:, 1].cpu().numpy()

    result_img = postprocess_output(output)
    img_io = io.BytesIO()
    result_img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
