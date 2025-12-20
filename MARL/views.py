from django.shortcuts import render
from django.http import JsonResponse
from .src.interface import start_training_thread

def start_training(request):
    start_training_thread()
    return JsonResponse({"status": "started"})

# def ui(request):
#     return render(request, 'backend/MARL/test.html')