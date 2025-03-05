import threading
from datetime import datetime

from scapy.all import sniff
from scapy.layers.inet import IP
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time
from .models import AnomalyLog


packet_history = []
start_time = time.time()
total_packets_sent = 0
total_packets_received = 0

LATENCY_THRESHOLD = 0.5
JITTER_THRESHOLD = 0.5
PACKET_LOSS_THRESHOLD = 0.5
BANDWIDTH_THRESHOLD = 1200


def calculate_metrics():
    global start_time, total_packets_received, packet_history
    # print(packet_history)

    if len(packet_history) < 2:
        return

    current_packet = packet_history[-1]
    previous_packet = packet_history[-2]

    latency = current_packet['timestamp'] - previous_packet['timestamp']
    jitter = abs(
        latency - (previous_packet['timestamp'] - packet_history[-3]['timestamp'] if len(packet_history) > 2 else 0))

    packet_loss = 0
    if total_packets_sent > 0:
        packet_loss = ((total_packets_sent - total_packets_received) / total_packets_sent) * 100

    # Calculate bandwidth (in bytes per second)
    time_elapsed = time.time() - start_time
    total_data = sum(p['length'] for p in packet_history)
    bandwidth = total_data / time_elapsed

    return {
        'latency': latency,
        'jitter': jitter,
        'packet_loss': packet_loss,
        'bandwidth': bandwidth
    }

def packet_handler(packet):
    global total_packets_received, start_time

    if packet.haslayer(IP):
        packet_data = {
            'timestamp': time.time(),
            'source_ip': packet[IP].src,
            'dest_ip': packet[IP].dst,
            'length': len(packet),
            'protocol': packet[IP].proto
        }
        # print(packet_data)
        packet_history.append(packet_data)
        total_packets_received += 1

        matrices = calculate_metrics()
        # print(matrices)
        if matrices is None:
            return
        anomaly = (matrices['latency'] > LATENCY_THRESHOLD or
                   matrices['jitter'] > JITTER_THRESHOLD or
                   matrices['packet_loss'] > PACKET_LOSS_THRESHOLD or
                   matrices['bandwidth'] > BANDWIDTH_THRESHOLD)

        if anomaly:
            AnomalyLog.objects.create(
                source_ip=packet_data['source_ip'],
                destination_ip=packet_data['dest_ip'],
                protocol=packet_data['protocol'],
                length=packet_data['length'],
                latency=matrices['latency'],
                jitter=matrices['jitter'],
                packet_loss=matrices['packet_loss'],
                bandwidth=matrices['bandwidth']
            )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "network_monitors",
            {
                "type": "network.update",
                "data": {
                    "packet": packet_data,
                    "metrics": matrices,
                    "anomaly": anomaly
                }
            }
        )

def start_sniffer():
    thread = threading.Thread(
        target=sniff,
        kwargs={'prn': packet_handler, 'store': 0, 'filter': 'ip'},
        daemon=True
    )
    thread.start()