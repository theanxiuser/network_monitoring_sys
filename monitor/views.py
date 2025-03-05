from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from monitor.models import AnomalyLog

@login_required
def dashboard(request):
    return render(request, 'monitor/dashboard.html')


@login_required
def anomaly_logs(request):
    logs = AnomalyLog.objects.all().order_by('-timestamp')[:50]
    return render(request, 'monitor/logs.html', {'logs': logs})