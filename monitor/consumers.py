from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.serializers import serialize
import json
# from .models import AnomalyLog

# class AnomalyLogConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         # if self.scope["user"].is_anonymous:
#         #     await self.close()
#         # else:
#         await self.channel_layer.group_add("anomaly_logs", self.channel_name)
#         await self.accept()
#
#         latest_logs = await self.get_latest_anomaly_logs(2)
#
#         # Send the latest logs to the client
#         await self.send(text_data=json.dumps({
#             'type': 'initial_data',
#             'data': latest_logs,
#         }))
#
#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard("anomaly_logs", self.channel_name)
#
#     async def anomaly_log_update(self, event):
#         await self.send(text_data=json.dumps(event['data']))
#
#     @sync_to_async
#     def get_latest_anomaly_logs(self, limit):
#         logs = AnomalyLog.objects.all().order_by('-timestamp')[:limit]
#         serialized_logs = serialize('json', logs)
#         return json.loads(serialized_logs)


class NetworkConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # if self.scope["user"].is_anonymous:
        #     await self.close()
        # else:
        await self.channel_layer.group_add("network_monitors", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("network_monitors", self.channel_name)

    async def network_update(self, event):
        await self.send(text_data=json.dumps(event['data']))