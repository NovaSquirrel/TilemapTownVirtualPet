import json
from pet_shared import *

entity_request_count = 1

class Pet(object):
	def __init__(self, town):
		self.entity_id = None
		self.entity_requested = False
		self.town = town

	async def create_entity(self):
		global entity_request_count

		async def created(id):
			print("created "+str(id))
			self.entity_id = id
			self.town.pets_by_entity_id[id] = self
			await self.town.send_command("BAG", {'update': {"id": id, "name": "A virtual pet!"}})
			await self.town.send_cmd_command(f'message_forwarding set {self.entity_id} MSG,PRI')
			await self.town.send_cmd_command(f'e {self.entity_id} drop')

		if self.entity_requested:
			return
		self.entity_requested = True

		request_name = 'temp_entity_' + str(entity_request_count)
		self.town.callbacks_for_creates[request_name] = created
		await self.town.send_command("BAG", {'create': {"name": request_name, "temp": True, "type": "generic"}})
		entity_request_count += 1

	async def send_cmd_command(self, command):
		if self.entity_id == None:
			return
		await self.town.send_command("CMD", {"text": command, "rc": self.entity_id})

	async def forward_message_to(self, message):
		if len(message)<3:
			return

		message_type = message[0:3]
		arg = {}
		if len(message) > 4:
			arg = json.loads(message[4:])

		if message_type == "MSG":
			if "buttons" in arg:
				for command in arg["buttons"][1::2]:
					if command.startswith('tpaccept '):
						await self.send_cmd_command(command)
