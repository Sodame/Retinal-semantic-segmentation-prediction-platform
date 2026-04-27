# Project Setup

## 1. Download and Set Up the Database
1. Download and install **MySQL**.
2. Create a new database named `new_schema_1`.
3. Import the provided `.sql` file into `new_schema_1`. This will populate the database with the following tables:
   - **Users table**
   - **Prediction history table**

[Download SQL file here](https://www.dropbox.com/scl/fo/il0yvy6skdfes6ci12hgj/AEb4EdAkEID8BAZInfxagnU?rlkey=fpie5neb342pd3zb10azz3adx&st=thhzv8nb&dl=0)

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
- [Download model weights from Dropbox](https://www.dropbox.com/scl/fo/ssowbb6ium7b5eu73s5sd/ADQGzC1ZFnkIJU597pBgiDE?rlkey=of8rspjhkkfrjygy5nhv2mi4u&st=arxbt1nx&dl=0).
- After downloading, place the two model weight files into the `modelWeight` folder located in the project's root directory.

## 4. Build and Run the Docker Containers
In the project root directory, open a terminal and run the following commands:

```bash
docker-compose build
docker-compose up
