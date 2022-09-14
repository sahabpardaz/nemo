import logging
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth.models import User
from apps.oidc_authentication.constants import openid_user_info_feilds

logger = logging.getLogger(__name__)

class AuthBackend(OIDCAuthenticationBackend):
    def filter_users_by_claims(self, claims):
        user, created = User.objects.update_or_create(
            username = claims.get(openid_user_info_feilds.USERNAME,''),
            defaults = {
                'email': claims.get(openid_user_info_feilds.EMAIL),
                'first_name': claims.get(openid_user_info_feilds.FIRST_NAME, ''),
                'last_name': claims.get(openid_user_info_feilds.LAST_NAME, '')
            }
        )
        if created:
            logger.info(f'A new user with username: {user.username} created.')

        return [user]
