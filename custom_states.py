from aiogram.dispatcher.filters.state import State, StatesGroup


class EnterLink(StatesGroup):
    enter_link = State()
