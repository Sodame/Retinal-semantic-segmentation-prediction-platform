import requests

# Flask 服务器的地址和端口
url = "http://localhost:5000/predict"

# 图片路径
image_path = r"C:\Users\56297\OneDrive\Desktop\capstone-project-2024-t3-9900f16asuperlu-master - 副本\uploads\20241003_223130_32_training.tif"

# 打开图片并发送 POST 请求
with open(image_path, 'rb') as img_file:
    files = {'file': img_file}
    response = requests.post(url, files=files)

    if response.status_code == 200:
        # 保存返回的图片结果
        result_path = r"D:\9900_2\new-type\results\binary_result.png"
        with open(result_path, 'wb') as f:
            f.write(response.content)
        print(f"Result saved to {result_path}")
    else:
        print(f"Failed to get prediction: {response.status_code}, {response.text}")
