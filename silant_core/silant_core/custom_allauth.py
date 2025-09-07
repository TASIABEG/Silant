from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings

class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        """
        Запрещает самостоятельную регистрацию пользователей.
        Только администратор может создавать пользователей через админ-панель.
        """
        return False