import time
from scheduler import retrain_model  # bạn tách phần train vào file này

while True:
    print("🔄 Retraining model...")
    retrain_model()
    print("✅ Model retrained.")
    time.sleep(600)  # 10 phút
