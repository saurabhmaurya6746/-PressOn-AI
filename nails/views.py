import os
import base64
import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.base import ContentFile

from .models import HandMeasurement


FASTAPI_URL = os.environ.get(
    "FASTAPI_URL",
    "https://presson-ai-backend.onrender.com/process-image/"
)


def home(request):

    if request.method == "POST":

        image = request.FILES.get("image")
        webcam_data = request.POST.get("webcam_image")

        if webcam_data:
            try:
                fmt, imgstr = webcam_data.split(";base64,")
                ext = fmt.split("/")[-1]

                image = ContentFile(
                    base64.b64decode(imgstr),
                    name=f"captured_hand.{ext}"
                )

            except Exception as e:
                print("Webcam decode error:", e)

        if image:
            obj = HandMeasurement.objects.create(image=image)
            return redirect("result", pk=obj.id)

    return render(request, "index.html")


def result(request, pk):

    obj = get_object_or_404(HandMeasurement, id=pk)

    coin_detected = False
    landmark_count = 0
    identified_fingers = []
    processed_image_url = ""

    try:
        original_image_url = obj.image.url
    except Exception:
        original_image_url = ""

    try:

        image_path = obj.image.path

        if not os.path.exists(image_path):
            raise FileNotFoundError(image_path)

        with open(image_path, "rb") as f:

            files = {
                "file": (
                    os.path.basename(image_path),
                    f,
                    "image/jpeg"
                )
            }

            response = requests.post(
                FASTAPI_URL,
                files=files,
                timeout=60
            )

        print("FastAPI Status:", response.status_code)

        if response.status_code == 200:

            res_json = response.json()

            print(res_json)

            if res_json.get("status") == "success":

                coin_detected = res_json.get(
                    "coin_detected",
                    False
                )

                landmark_count = res_json.get(
                    "landmark_count",
                    0
                )

                identified_fingers = res_json.get(
                    "identified_fingers",
                    []
                )

                processed_image_url = res_json.get(
                    "processed_image",
                    ""
                )

        else:

            print("FastAPI Error")
            print(response.text)

    except Exception as e:

        print("=" * 60)
        print("RESULT VIEW ERROR")
        print(e)
        print("=" * 60)

    if not processed_image_url:
        processed_image_url = original_image_url

    print("Image Present:", bool(processed_image_url))
    context = {
        "obj": obj,
        "original_image_url": original_image_url,
        "processed_image": processed_image_url,
        "identified_fingers": identified_fingers,
        "landmark_count": landmark_count,
        "coin_detected": coin_detected,
    }
    
    return render(request, "result.html", context)
