import logging
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import ChannelPrivateError, InviteHashExpiredError

logger = logging.getLogger(__name__)

class ChannelJoiner:
    @staticmethod
    async def ensure_joined(client, channel_username):
        """
        Ensure the bot has joined the specified channel.
        Handle cases where the bot is already a member.
        """
        try:
            logger.info(f"Attempting to join channel: {channel_username}")
            # This will join the channel if not already joined. 
            # If already joined, it typically succeeds without doing much, 
            # but we can also check membership if needed.
            await client(JoinChannelRequest(channel_username))
            logger.info(f"Successfully joined/confirmed membership in: {channel_username}")
            return True
        except ChannelPrivateError:
            logger.error(f"Cannot join {channel_username}: It is a private channel.")
        except InviteHashExpiredError:
            logger.error(f"Cannot join {channel_username}: Invite link expired.")
        except Exception as e:
            logger.error(f"Failed to join {channel_username}: {e}")
        
        return False
