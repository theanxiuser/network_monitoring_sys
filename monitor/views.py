from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

def dashboard(request):
    return render(request, 'monitor/dashboard.html')