import os
from django.conf import settings
from django.shortcuts import render, redirect
from .models import HandMeasurement

# AI & Utils Imports
from utils.hand_detector import detect_hand
from ai.inference import predict_nails
from utils.finger_identifier import identify_fingers
from utils.coin_detector import get_pixel_to_mm_ratio  # 🔴 Coin Tracker Import

import base64
from django.core.files.base import ContentFile

def home(request):
    if request.method == "POST":
        image = request.FILES.get("image")
        webcam_data = request.POST.get("webcam_image") # Live camera base64 data

        # Agar user ne Live Camera se photo kheenchi hai
        if webcam_data:
            format, imgstr = webcam_data.split(';base64,') 
            ext = format.split('/')[-1] 
            image = ContentFile(base64.b64decode(imgstr), name=f"captured_hand.{ext}")

        if image:
            obj = HandMeasurement.objects.create(image=image)
            return redirect("result", pk=obj.id)

    return render(request, "index.html")

# views.py (Updated with Fail-Safe Alert Flag)
import os
import cv2
from django.conf import settings
from django.shortcuts import render, redirect
from .models import HandMeasurement

# AI & Utils Imports
from utils.hand_detector import detect_hand
from ai.inference import predict_nails
from utils.finger_identifier import identify_fingers
from utils.coin_detector import get_pixel_to_mm_ratio

# views.py me result function ka updated hissa
def result(request, pk):
    obj = HandMeasurement.objects.get(id=pk)
    image_path = obj.image.path

    processed_filename = "processed_" + os.path.basename(image_path)
    output_path = os.path.join(settings.MEDIA_ROOT, processed_filename)

    landmarks = detect_hand(image_path, output_path)

    # 1. Ratio aur Coin Data fetch kiya
    pixels_per_mm, coin_data = get_pixel_to_mm_ratio(image_path, real_coin_diameter_mm=27.0)

    result_data = predict_nails(image_path)
    target_img_path = result_data.get("processed_image", output_path)

    # Default values
    coin_detected = True
    identified_fingers = []

    # 2. 🔴 CHECK: Agar coin detect hua hai, tabhi aage badhein
    if coin_data:
        # Draw coin circle
        if os.path.exists(target_img_path):
            processed_img = cv2.imread(target_img_path)
            if processed_img is not None:
                cv2.circle(processed_img, coin_data["center"], coin_data["radius"], (255, 0, 0), 3)
                cv2.circle(processed_img, coin_data["center"], 4, (0, 0, 255), -1)
                cv2.putText(processed_img, f"Coin: {coin_data['diameter_px']}px", 
                            (coin_data["center"][0] - coin_data["radius"], coin_data["center"][1] - coin_data["radius"] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                cv2.imwrite(target_img_path, processed_img)

        # Pixels ko real MM me convert karein
        if result_data and "measurements" in result_data:
            for nail in result_data["measurements"]:
                nail["width_mm"] = round(nail["width_px"] / pixels_per_mm, 2)
                nail["height_mm"] = round(nail["height_px"] / pixels_per_mm, 2)

        # Sizing aur identification logic run karein
        identified_fingers = identify_fingers(landmarks, result_data["measurements"])
    else:
        # Coin nahi mila
        coin_detected = False

    processed_image_url = None
    if result_data.get("processed_image"):
        relative_path = os.path.relpath(result_data["processed_image"], settings.MEDIA_ROOT)
        processed_image_url = settings.MEDIA_URL + relative_path

    landmark_count = len(landmarks) if landmarks else 0

    context = {
        "obj": obj,
        "result": result_data,
        "identified_fingers": identified_fingers,
        "processed_image": processed_image_url,
        "landmark_count": landmark_count,
        "coin_detected": coin_detected,
    }

    return render(request, "result.html", context)