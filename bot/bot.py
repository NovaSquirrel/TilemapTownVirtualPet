#!/usr/bin/env python
import asyncio
from pet_shared import *
from tilemap_town import TilemapTown
from pet_entity import Pet

async def main():
	async with asyncio.TaskGroup() as tg:
		town = TilemapTown('wss://novasquirrel.com/townws/')
		tg.create_task(town.run_timer())
		tg.create_task(town.run_client())

asyncio.run(main())
