from fastapi import FastAPI, File, UploadFile
from onnxruntime import InferenceSession
import numpy as np
import cv2

from .utils import (
    preprocess_image, 
    filter_detections, 
    rescale_back
)


app = FastAPI()
model_path = "./model/best.onnx"
session = InferenceSession(model_path, providers=["CPUExecutionProvider"])


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # Read and preprocess the image
    image = await file.read()
    image = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)

    height, width, _ = image.shape

    # preprocess image
    image = preprocess_image(image)
    print("image_shape: ", image.shape)

    # Run inference
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    results = session.run([output_name], {input_name: image})
    print("pred_shape: ", results[0].shape)

    # Postprocess results
    detected_box = filter_detections(results[0][0].transpose())
    boxes, confidence = rescale_back(detected_box, width, height)

    return {
        "boxes": [box.tolist() for box in boxes],
        "confidences": [round(c, 2) for c in confidence]
    }
