import threading
from scapy.all import sniff
from scapy.layers.inet import IP
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def packet_handler(packet):
    if packet.haslayer(IP):
        data = {
            'source_ip': packet[IP].src,
            'dest_ip': packet[IP].dst,
            'protocol': packet[IP].proto,
        }
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "network_monitors",
            {
                "type": "network.update",
                "data": data
            }
        )

def start_sniffer():
    thread = threading.Thread(
        target=sniff,
        kwargs={'prn': packet_handler, 'store': 0, 'filter': 'ip'},
        daemon=True
    )
    thread.start()