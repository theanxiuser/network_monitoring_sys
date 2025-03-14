import json
import threading
from datetime import datetime, timedelta

from scapy.all import sniff
from scapy.layers.inet import IP, TCP, UDP
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time
from .models import AnomalyLog
from decouple import config
from django.db.models import Count


packet_history = []
start_time = time.time()
total_packets_sent = 0
total_packets_received = 0

total_uplink_data = 0
total_downlink_data = 0

LATENCY_THRESHOLD = 0.5
JITTER_THRESHOLD = 0.5
PACKET_LOSS_THRESHOLD = 0.5
BANDWIDTH_THRESHOLD = 1200


LOCAL_IP = config('LOCAL_IP')


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
    uplink_bandwidth = total_uplink_data / time_elapsed
    downlink_bandwidth = total_downlink_data / time_elapsed

    return {
        'latency': latency,
        'jitter': jitter,
        'packet_loss': packet_loss,
        'bandwidth': bandwidth,
        'uplink_bandwidth': uplink_bandwidth,
        'downlink_bandwidth': downlink_bandwidth
    }

def packet_handler(packet):
    global total_packets_received, total_uplink_data, total_downlink_data

    if packet.haslayer(IP):
        protocol = 'TCP' if packet.haslayer(TCP) else 'UDP' if packet.haslayer(UDP) else 'Other'
        packet_data = {
            'timestamp': time.time(),
            'source_ip': packet[IP].src,
            'dest_ip': packet[IP].dst,
            'length': len(packet),
            'protocol': protocol
        }

        if packet[IP].src == LOCAL_IP:
            total_uplink_data += len(packet)
        else:
            total_downlink_data += len(packet)

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
                   matrices['bandwidth'] > 2 * BANDWIDTH_THRESHOLD)

        anomalies = {
            'latency_anomaly': matrices['latency'] > LATENCY_THRESHOLD,
            'jitter_anomaly': matrices['jitter'] > JITTER_THRESHOLD,
            'packet_loss_anomaly': matrices['packet_loss'] > PACKET_LOSS_THRESHOLD,
            'uplink_bandwidth_anomaly': matrices['uplink_bandwidth'] > BANDWIDTH_THRESHOLD,
            'downlink_bandwidth_anomaly': matrices['downlink_bandwidth'] > BANDWIDTH_THRESHOLD
        }

        if any(anomalies.values()):
            AnomalyLog.objects.create(
                source_ip=packet_data['source_ip'],
                destination_ip=packet_data['dest_ip'],
                protocol=packet_data['protocol'],
                length=packet_data['length'],
                latency=matrices['latency'],
                jitter=matrices['jitter'],
                packet_loss=matrices['packet_loss'],
                bandwidth=matrices['bandwidth'],
                uplink_bandwidth=matrices['uplink_bandwidth'],
                downlink_bandwidth=matrices['downlink_bandwidth'],
                anomaly_type=', '.join([k for k, v in anomalies.items() if v])
            )

        # print(
        #     f"packet_data: {packet_data}\
        #     metrics: {matrices}\
        #     anomalies: {anomalies}\n"
        # )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "network_monitors",
            {
                "type": "network.update",
                "data": {
                    "packet": packet_data,
                    "metrics": matrices,
                    "anomaly": anomaly,
                    "anomalies": anomalies,
                    "week_anomalies": get_weekly_anomalies()
                }
            }
        )

def get_weekly_anomalies():
    one_week_ago = datetime.now() - timedelta(days=7)
    anomalies = AnomalyLog.objects.filter(timestamp__gte=one_week_ago).values('anomaly_type').annotate(count=Count('anomaly_type'))
    return list(anomalies)


def start_sniffer(iface):
    thread = threading.Thread(
        target=sniff,
        kwargs={'prn': packet_handler, 'store': 0, 'filter': 'ip', 'iface': iface, 'promisc': True},
        daemon=True
    )
    thread.start()