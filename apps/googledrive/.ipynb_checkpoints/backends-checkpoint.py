# from django.conf import settings
from client import GoogleDriveClient
# from .client import GoogleDriveClient


class DefaultGoogleDriveClient(object):
    """A singleton class for accessing system user's google drive resource by giving a pre-generated refresh token"""
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = GoogleDriveClient.load_from_dict({
                'client_id': '120258693079-kqi04l6u7k0p25aaeg2lv8gcmlovlbuh.apps.googleusercontent.com',
                'client_secret': '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',
                'refresh_token': '1//0edwqKSQRid6QCgYIARAAGA4SNwF-L9Ir5uzJI7SV5ruRYT9gjCafooIbObUMV_dcl7SJ1CFjiKHx-idwm-9AdbKRu7PDui0SFL0',
                
            })
        return cls._instance
