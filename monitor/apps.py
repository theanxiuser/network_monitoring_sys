from django.apps import AppConfig
from decouple import config

iface = config('NETWORK_INTERFACE', 'wlp2s0')

class MonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitor'


    def ready(self):
        from .sniffer import start_sniffer
        start_sniffer(iface=iface)
