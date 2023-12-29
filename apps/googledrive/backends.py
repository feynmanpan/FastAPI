# from django.conf import settings
from .client import GoogleDriveClient
# from .client import GoogleDriveClient


class DefaultGoogleDriveClient(object):
    """A singleton class for accessing system user's google drive resource by giving a pre-generated refresh token"""
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = GoogleDriveClient.load_from_dict({
                'client_id': '120258693079-36o6alf3qp6rimtu6l4jkn0ki1s3gf5p.apps.googleusercontent.com',
                'client_secret': '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',
                'refresh_token': "1//0eVoEicR7NH27CgYIARAAGA4SNwF-L9IrYVH3cCpnD7kKctj6T5Q0x6XNNBSe2W_RO52gLs1Hbyr0u9OWGj3VZuAwkkA4iQmHyJQ",
            })
        return cls._instance
