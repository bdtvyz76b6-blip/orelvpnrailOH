from aiogram.fsm.state import State, StatesGroup


class PromoStates(StatesGroup):
    waiting_promo = State()


class BroadcastStates(StatesGroup):
    waiting_text = State()
