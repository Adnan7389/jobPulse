from aiogram.fsm.state import State, StatesGroup

class OnboardingStates(StatesGroup):
    """FSM states for user onboarding flow"""
    waiting_for_skills = State()
    waiting_for_job_titles = State()
    waiting_for_experience_level = State()
    waiting_for_years_experience = State()
    waiting_for_preferred_category = State()
    waiting_for_preferred_mode = State()
    waiting_for_preferred_type = State()
    waiting_for_bio = State()
