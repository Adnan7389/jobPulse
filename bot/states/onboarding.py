from aiogram.fsm.state import State, StatesGroup

class OnboardingStates(StatesGroup):
    """FSM states for user onboarding flow"""
    waiting_for_bio = State()
    waiting_for_preferred_category = State()
    waiting_for_experience_level = State()
    waiting_for_channels = State()
