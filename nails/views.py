import os
import base64
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from .models import HandMeasurement

# 🚀 FastAPI URL Definition
FASTAPI_URL = os.environ.get("FASTAPI_URL", "https://presson-ai-backend.onrender.com/process-image/")

def home(request):
    if request.method == "POST":
        image = request.FILES.get("image")
        webcam_data = request.POST.get("webcam_image")  # Live camera base64 data

        # Agar user ne Live Camera se photo kheenchi hai
        if webcam_data:
            try:
                format, imgstr = webcam_data.split(';base64,') 
                ext = format.split('/')[-1] 
                image = ContentFile(base64.b64decode(imgstr), name=f"captured_hand.{ext}")
            except Exception as e:
                print(f"Webcam data parsing error: {e}")

        if image:
            obj = HandMeasurement.objects.create(image=image)
            return redirect("result", pk=obj.id)

    return render(request, "index.html")
 def result(request, pk):
    obj = HandMeasurement.objects.get(id=pk)
    image_path = obj.image.path

    coin_detected = False
    identified_fingers = []
    processed_image_url = None
    landmark_count = 0

    try:
        with open(image_path, 'rb') as f:
            file_data = f.read()

        files = {
            'file': (os.path.basename(image_path), file_data, 'image/jpeg')
        }

        response = requests.post(FASTAPI_URL, files=files, timeout=25)
        print(f"DEBUG: FastAPI Response Status Code: {response.status_code}")

        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("status") == "success":
                coin_detected = res_json.get("coin_detected", False)
                landmark_count = res_json.get("landmark_count", 0)
                identified_fingers = res_json.get("identified_fingers", [])
                processed_image_url = res_json.get("processed_image", obj.image.url)
        else:
            print(f"FastAPI Server Error Status: {response.status_code}")

        except Exception as e:
            print(f"DEBUG: Handled Exception during FastAPI call: {e}")
    
        if not processed_image_url:
            processed_image_url = obj.image.url
    
        context = {
            "obj": obj,
            "identified_fingers": identified_fingers,
            "processed_image": processed_image_url,
            "landmark_count": landmark_count,
            "coin_detected": coin_detected,
        }
        return render(request, "result.html", context)
