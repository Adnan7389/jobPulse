from aiogram.fsm.state import State, StatesGroup

class ChannelStates(StatesGroup):
    """FSM states for channel management flow"""
    waiting_for_channel = State()
