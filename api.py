from fastapi import FastAPI
from scheduler import retrain_model  # Giả sử mã bạn đưa nằm trong file retrain.py
from utils import log

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Model retraining API is running."}


@app.post("/retrain")
def retrain():
    try:
        log("API retrain_model called.")
        retrain_model()
        return {"status": "success", "message": "Model retrained successfully."}
    except Exception as e:
        log(f"Error during retraining: {e}")
        return {"status": "error", "message": str(e)}
