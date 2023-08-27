#!/usr/bin/env python
import asyncio, json, websockets

bot_prefix = "!"

# .----------------------------------------------
# | Command registration
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
# | Utilities
# '----------------------------------------------

async def send_command(command, params):
	def make_protocol_message_string(command, params):
		if params != None:
			return command + " " + json.dumps(params)
		return command
	await websocket.send(make_protocol_message_string(command, params))

def separate_first_word(text, lowercase_first=True):
	space = text.find(" ")
	command = text
	arg = ""
	if space >= 0:
		command = text[0:space]
		arg = text[space+1:]
	if lowercase_first:
		command = command.lower()
	return (command, arg)

# .----------------------------------------------
# | Chat commands
# '----------------------------------------------

@chat_command()
async def fn_fire(arg):
	await send_command("CMD", {"text": "userpic fire"})
	return "🔥"

@chat_command()
async def fn_cat(arg):
	await send_command("CMD", {"text": "userpic cat"})
	return "🐈"

@chat_command()
async def fn_hamster(arg):
	await send_command("CMD", {"text": "userpic hamster"})
	return "🐹"

@chat_command()
async def fn_bunny(arg):
	await send_command("CMD", {"text": "userpic bunny"})
	return "🐇"

@chat_command()
async def fn_echo(arg):
	return arg

@chat_command()
async def fn_double(arg):
	if arg.isdigit():
		return str(int(arg) * 2)
	return "Not a number"

@chat_command()
async def fn_allcommands(arg):
	return " ".join(chat_command_handlers.keys())

# Call the handler for a chat command
async def handle_chat_command(text):
	if not text.startswith(bot_prefix):
		return
	text = text[len(bot_prefix):]
	command, arg = separate_first_word(text)
	if command in chat_command_handlers:
		return await chat_command_handlers[command](arg)
	return "Unknown command"

# .----------------------------------------------
# | Protocol message handlers
# '----------------------------------------------

@protocol_command()
async def fn_PIN(arg):
	await websocket.send("PIN")

@protocol_command()
async def fn_MSG(arg):
	if "name" not in arg: # Ignore server messages
		return
	response = await handle_chat_command(arg["text"])
	if response != None:
		await send_command("MSG", {"text": response})

@protocol_command()
async def fn_PRI(arg):
	response = await handle_chat_command(arg["text"])
	if response != None:
		await send_command("CMD", {"text": f'tell {arg["username"]} {response}'})

# .----------------------------------------------
# | Websocket connection
# '----------------------------------------------

async def run_timer():
	while True:
		await asyncio.sleep(1)

async def receive_server_message(message):
	message_type = message[0:3]
	arg = {}
	if len(message) > 4:
		arg = json.loads(message[4:])
	if message_type in protocol_handlers:
		await protocol_handlers[message_type](arg)

async def run_client():
	global websocket

	async for websocket in websockets.connect(uri="wss://novasquirrel.com/townws/"):
		try:
			await send_command("IDN", {
				"bot": True,
				"name": "Bot test",
				"features": {
					"batch": {"version": "0.0.1"}
				}
			})
			async for message in websocket:
				# Split the message into parts
				if len(message)<3:
					continue
				if message[0:4] == "BAT ":
					for sub_message in message[4:].splitlines():
						await receive_server_message(sub_message)
				else:
					await receive_server_message(message)

		except websockets.ConnectionClosed:
			print("Connection closed")
			continue

async def main():
	async with asyncio.TaskGroup() as tg:
		timer_task = tg.create_task(run_timer())
		client_task = tg.create_task(run_client())

asyncio.run(main())
