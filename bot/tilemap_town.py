# Tilemap Town connection
from pet_shared import *
from pet_entity import Pet
import asyncio, json, websockets

bot_prefix = "pet."

# .----------------------------------------------
# | Tilemap Town class
# '----------------------------------------------

class TilemapTown(object):
	def __init__(self, uri):
		self.entity_id = None
		self.websocket = None
		self.uri = uri
		self.callbacks_for_creates = {}

		self.pets = set()
		self.pets_by_entity_id = {}

	# .----------------------------------------------
	# | Websocket connection
	# '----------------------------------------------

	async def run_client(self):
		async for self.websocket in websockets.connect(uri=self.uri):
			try:
				await self.send_command("IDN", {
					"bot": True,
					"name": "Bot test",
					"features": {
						"batch": {"version": "0.0.1"},
						"entity_message_forwarding": {"version": "0.0.1"},
					}
				})
				async for message in self.websocket:
					# Split the message into parts
					if len(message)<3:
						continue
					if message[0:4] == "FWD ":
						entity, forward_message = separate_first_word(message[4:], lowercase_first=False)
						if entity not in self.pets_by_entity_id:
							print("Unrecognized entity ID "+entity)
						if forward_message[0:4] == "BAT ":
							for sub_message in forward_message[4:].splitlines():
								await self.pets_by_entity_id[entity].forward_message_to(sub_message)
						else:
							await self.pets_by_entity_id[entity].forward_message_to(forward_message)
					elif message[0:4] == "BAT ":
						for sub_message in message[4:].splitlines():
							await self.receive_server_message(sub_message)
					else:
						await self.receive_server_message(message)

			except websockets.ConnectionClosed:
				print("Connection closed")
				continue

	async def receive_server_message(self, message):
		print("<< "+message)
		message_type = message[0:3]
		arg = {}
		if len(message) > 4:
			arg = json.loads(message[4:])
		if message_type in protocol_handlers:
			await protocol_handlers[message_type](self, arg)

	async def send_command(self, command, params):
		print(">> "+command)
		if self.websocket == None:
			return
		def make_protocol_message_string(command, params):
			if params != None:
				return command + " " + json.dumps(params)
			return command
		await self.websocket.send(make_protocol_message_string(command, params))

	async def send_cmd_command(self, command):
		await self.send_command("CMD", {"text": command})

	# .----------------------------------------------
	# | Manage timed events
	# '----------------------------------------------

	async def run_timer(self):
		while True:
			await asyncio.sleep(1)

# -----------------------------------------------------------------------------

# .----------------------------------------------
# | Handle registration
# '----------------------------------------------

protocol_handlers = {}
def protocol_command():
	def decorator(f):
		command_name = f.__name__[3:]
		protocol_handlers[command_name] = f
	return decorator

chat_command_handlers = {}
def chat_command():
	def decorator(f):
		command_name = f.__name__[3:]
		chat_command_handlers[command_name] = f
	return decorator

# .----------------------------------------------
# | Chat commands
# '----------------------------------------------

@chat_command()
async def fn_fire(self, arg):
	await send_command("CMD", {"text": "userpic fire"})
	return "🔥"

@chat_command()
async def fn_cat(self, arg):
	await send_command("CMD", {"text": "userpic cat"})
	return "🐈"

@chat_command()
async def fn_hamster(self, arg):
	await send_command("CMD", {"text": "userpic hamster"})
	return "🐹"

@chat_command()
async def fn_bunny(self, arg):
	await send_command("CMD", {"text": "userpic bunny"})
	return "🐇"

@chat_command()
async def fn_echo(self, arg):
	return arg

@chat_command()
async def fn_double(self, arg):
	if arg.isdigit():
		return str(int(arg) * 2)
	return "Not a number"

@chat_command()
async def fn_allcommands(self, arg):
	return " ".join(chat_command_handlers.keys())

# Call the handler for a chat command
async def handle_chat_command(self, text):
	if not text.startswith(bot_prefix):
		return
	text = text[len(bot_prefix):]
	command, arg = separate_first_word(text)
	if command in chat_command_handlers:
		return await chat_command_handlers[command](self, arg)
	return "Unknown command"

# .----------------------------------------------
# | Protocol message handlers
# '----------------------------------------------

@protocol_command()
async def fn_PIN(self, arg):
	await self.send_command("PIN", None)

@protocol_command()
async def fn_MSG(self, arg):
	if "name" not in arg: # Ignore server messages
		return
	response = await handle_chat_command(arg["text"])
	if response != None:
		await send_command("MSG", {"text": response})

@protocol_command()
async def fn_PRI(self, arg):
	response = await handle_chat_command(arg["text"])
	if response != None:
		await send_command("CMD", {"text": f'tell {arg["username"]} {response}'})

@protocol_command()
async def fn_BAG(self, arg):
	if "list" in arg and "container" in arg["list"] and (arg["list"]["container"] != self.entity_id):
		return
	if "create" in arg and "id" in arg["create"] and "name" in arg["create"]:
		id = arg["create"]["id"]
		name = arg["create"]["name"]
		if name in self.callbacks_for_creates:
			await self.callbacks_for_creates[name](id)
			del self.callbacks_for_creates[name]

@protocol_command()
async def fn_WHO(self, arg):
	if "you" in arg:
		self.entity_id = arg["you"]
	if "new_id" in arg and arg["new_id"]["id"] == self.entity_id:
		self.entity_id = arg["new_id"]["new_id"]

@protocol_command()
async def fn_IDN(self, arg):
	print("Logged in")

	pet = Pet(self)
	await pet.create_entity()
	self.pets.add(pet)
