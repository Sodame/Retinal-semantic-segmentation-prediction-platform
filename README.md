# Project Setup

## 1. Download and Set Up the Database
1. Download and install **MySQL**.
2. Create a new database named `new_schema_1`.
3. Import the provided `.sql` file into `new_schema_1`. This will populate the database with the following tables:
   - **Users table**
   - **Prediction history table**

[Download SQL file here](https://www.dropbox.com/scl/fi/uf8ye6nt7fmquzfa98mhd/LadderNet_model.pth?rlkey=uzy12op502c66lhv2ip4cdqhe&st=n93uuj2x&dl=0)

## 2. Modify Database Configuration
In the project root directory, open the `config.py` file and update the database configuration. Modify the **username**, **password** to match your local MySQL setup.

Example configuration in `config.py`:
```python
USERNAME="your_username"
PASSWORD="your_password"
DATABASE= "new_schema_1"
```

## 3. Download Model Weights
Due to GitHub's file size limits, the model weight files are provided via a Dropbox link:
- [Download model weights from Dropbox](https://www.dropbox.com/scl/fi/uf8ye6nt7fmquzfa98mhd/LadderNet_model.pth?rlkey=uzy12op502c66lhv2ip4cdqhe&st=n93uuj2x&dl=0).
- After downloading, place the two model weight files into the `modelWeight` folder located in the project's root directory.

## 4. Build and Run the Docker Containers
In the project root directory, open a terminal and run the following commands:

```bash
docker-compose build
docker-compose up
