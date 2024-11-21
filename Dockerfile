FROM python:3.9-slim

# Cài đặt các gói cần thiết
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    && apt-get clean

# Tạo thư mục ứng dụng
WORKDIR /app

# Sao chép file dự án vào container
COPY . .

# Cài đặt các thư viện Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Chạy ứng dụng Flask
CMD ["python", "face_recognition_api.py"]
