import os
import base64
import requests  # FastAPI से बात करने के लिए
from django.conf import settings
from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from .models import HandMeasurement

# 💥 अपनी नई FastAPI का URL यहाँ डालो (आखिर में स्लैश / लगाना मत भूलना)
FASTAPI_URL = os.environ.get("FASTAPI_URL", "https://presson-ai-backend.onrender.com/process-image/")

def home(request):
    if request.method == "POST":
        image = request.FILES.get("image")
        webcam_data = request.POST.get("webcam_image")  # Live camera base64 data

        # Agar user ne Live Camera se photo kheenchi hai
        if webcam_data:
            format, imgstr = webcam_data.split(';base64,') 
            ext = format.split('/')[-1] 
            image = ContentFile(base64.b64decode(imgstr), name=f"captured_hand.{ext}")

        if image:
            obj = HandMeasurement.objects.create(image=image)
            return redirect("result", pk=obj.id)

    return render(request, "index.html")


def result(request, pk):
    obj = HandMeasurement.objects.get(id=pk)
    image_path = obj.image.path

    # डिफॉल्ट वैल्यूज
    coin_detected = False
    identified_fingers = []
    processed_image_url = None
    landmark_count = 0
    result_data = {"status": "failed"}

    try:
        # 1. इमेज को बाइनरी मोड में ओपन करना
        with open(image_path, 'rb') as f:
            file_data = f.read()
        
        # FastAPI को भेजने के लिए पेलोड तैयार करना
        files = {
            'file': (os.path.basename(image_path), file_data, 'image/jpeg')
        }

        # 2. 🚀 इमेज को सीधा FastAPI सर्वर पर भेजना (बिना किसी लोकल रैम लोड के)
        response = requests.post(FASTAPI_URL, files=files, timeout=60)
        
        if response.status_code == 200:
            result_data = response.json()
            
            # FastAPI से आया डेटा पार्स करना
            if result_data.get("status") == "success":
                coin_detected = result_data.get("coin_detected", True)
                identified_fingers = result_data.get("identified_fingers", [])
                landmark_count = result_data.get("landmark_count", 0)
                
                # अगर FastAPI ने प्रोसेस की हुई इमेज का base64 या URL दिया है
                if result_data.get("processed_image"):
                    processed_image_url = result_data.get("processed_image")
        else:
            print(f"FastAPI Server Error Status: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Could not connect to FastAPI Server: {e}")

    # अगर प्रोसेसिंग फ़ेल हुई या इमेज नहीं मिली, तो ओरिजिनल इमेज ही दिखा देंगे
    if not processed_image_url:
        processed_image_url = obj.image.url

    context = {
        "obj": obj,
        "result": result_data,
        "identified_fingers": identified_fingers,
        "processed_image": processed_image_url,
        "landmark_count": landmark_count,
        "coin_detected": coin_detected,
    }

    return render(request, "result.html", context)
