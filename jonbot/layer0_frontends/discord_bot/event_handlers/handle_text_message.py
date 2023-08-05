import logging
import uuid

import aiohttp
import discord

from jonbot.layer1_api_interface.app import API_CHAT_URL, API_CHAT_STREAM_URL
from jonbot.layer3_data_layer.data_models.conversation_models import ChatInput, ChatResponse, ChatRequest
from jonbot.layer3_data_layer.data_models.discord_message import DiscordMessageDocument
from jonbot.layer3_data_layer.database.mongo_database import mongo_database_manager

logger = logging.getLogger(__name__)




async def handle_text_message(message: discord.Message,
                              streaming: bool = False):
    async with aiohttp.ClientSession() as session:
        chat_input = ChatInput(message=message.content,
                               uuid=str(uuid.uuid4()),
                               )

        chat_request = ChatRequest(chat_input = chat_input)
        if streaming:
            api_route = API_CHAT_STREAM_URL
        else:
            api_route = API_CHAT_URL

        logger.info(f"Sending chat input: {chat_request}")

        async with session.post(api_route, json=chat_request.dict()) as response:
            if response.status == 200:
                data = await response.json()
                chat_response = ChatResponse(**data)
                await message.reply(chat_response.message)
                discord_message_document = DiscordMessageDocument.from_message(message=message).dict()
                mongo_database_manager.upsert( collection_name="discord_messages",
                                               data=discord_message_document,)
            else:
                error_message = f"Received non-200 response code: {response.status}"
                logger.exception(error_message)
                await message.reply(
                    f"Sorry, I'm currently unable to process your request. {error_message}")
