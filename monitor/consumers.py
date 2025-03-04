from channels.generic.websocket import AsyncWebsocketConsumer
import json

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