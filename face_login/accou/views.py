from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
import os
import cv2
import tempfile
from django.contrib.auth.models import User
from .models import UserImages
import face_recognition
import base64

@csrf_exempt
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        face_image_data = request.POST.get('face_image')

        if not username or not face_image_data:
            return JsonResponse({
                'status': 'error',
                'message': 'Username or face image is missing'
            }, status=400)

        try:
            if "," in face_image_data:
                face_image_data = face_image_data.split(",")[1]  # Extract base64 part
            face_image = ContentFile(base64.b64decode(face_image_data), name=f'{username}.jpg')
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid face image data: {str(e)}'
            }, status=400)

        try:
            user, created = User.objects.get_or_create(username=username)
            if not created and UserImages.objects.filter(user=user).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'User already registered'
                }, status=400)

            UserImages.objects.create(user=user, face_image=face_image)
            return JsonResponse({
                'status': 'success',
                'message': 'User registered successfully'
            }, status=201)

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error during registration: {str(e)}'
            }, status=500)

    return render(request, 'register.html')

@csrf_exempt
def login(request):
    if request.method == 'POST':
        face_image_data = request.POST.get('face_image')

        if not face_image_data:
            return JsonResponse({
                'status': 'error',
                'message': 'Face image is missing.'
            })

        try:
            if "," in face_image_data:
                face_image_data = face_image_data.split(",")[1]

            face_image = base64.b64decode(face_image_data)

            user_faces_dir = 'C:\\Users\\Nikhil Darji\\Documents\\Nikhil Darji\\flogin\\user_faces\\'
            os.makedirs(user_faces_dir, exist_ok=True)

            user_face_path = os.path.join(user_faces_dir, 'temp_user_face.jpg')

            with open(user_face_path, 'wb') as user_face_file:
                user_face_file.write(face_image)

            if not os.path.exists(user_face_path):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Temporary file could not be created.'
                })

            captured_face = face_recognition.load_image_file(user_face_path)
            captured_encoding = face_recognition.face_encodings(captured_face)

            os.remove(user_face_path)  # Cleanup

            if not captured_encoding:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No face detected in the image.'
                })
            captured_encoding = captured_encoding[0]

            users = UserImages.objects.all()
            for user in users:
                stored_face_path = user.face_image.path if user.face_image else None
                if not stored_face_path or not os.path.exists(stored_face_path):
                    continue  # Skip missing files

                stored_face = face_recognition.load_image_file(stored_face_path)
                stored_encoding = face_recognition.face_encodings(stored_face)

                if stored_encoding and face_recognition.compare_faces([stored_encoding[0]], captured_encoding)[0]:
                    return JsonResponse({
                        'status': 'success',
                        'message': f'Welcome back, {user.user.username}!'
                    })

            return JsonResponse({
                'status': 'error',
                'message': 'No matching face found. Please register first.'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error during login: {str(e)}'
            })

    return render(request, 'login.html')
