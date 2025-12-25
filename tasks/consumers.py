from channels.generic.websocket import AsyncJsonWebsocketConsumer


class WorkspaceConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.workspace = self.scope['url_route']['kwargs']['workspace']
        self.group_name = f'workspace_{self.workspace}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Accept client messages if needed for control; ignore by default
        pass

    async def task_update(self, event):
        # Event shape: {'type': 'task_update', 'payload': {...}}
        await self.send_json(event.get('payload', {}))
