

from rest_framework import authentication, exceptions
from django.conf import settings

class StaticTokenAuthentication(authentication.BaseAuthentication):
    keyword = 'Token'

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).split()

        if not auth_header or auth_header[0].decode().lower() != self.keyword.lower():
            return None

        if len(auth_header) == 1:
            msg = 'Formato de token inválido. Se espera "Token <token>".'
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth_header) > 2:
            msg = 'Formato de token inválido. Se espera "Token <token>".'
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth_header[1].decode()
        except UnicodeError:
            msg = 'Token inválido. No puede contener caracteres no válidos.'
            raise exceptions.AuthenticationFailed(msg)

        if token != settings.STATIC_API_TOKEN:
            raise exceptions.AuthenticationFailed('Token inválido.')

        user = type('User', (object,), {'is_authenticated': True})()

        return (user, None)
