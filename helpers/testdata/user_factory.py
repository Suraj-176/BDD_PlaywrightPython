from core.logger.logger import logger

class UserFactory:
    """
    Test Data Factory generating SauceDemo user credential datasets.
    """

    @staticmethod
    def valid_standard_user() -> dict:
        """
        Returns a standard valid SauceDemo user.
        """
        return {
            "username": "standard_user",
            "password": "secret_sauce",
        }

    @staticmethod
    def invalid_username() -> dict:
        """
        Returns credentials with an invalid username.
        """
        return {
            "username": "invalid_user",
            "password": "secret_sauce",
        }

    @staticmethod
    def invalid_password() -> dict:
        """
        Returns credentials with an invalid password.
        """
        return {
            "username": "standard_user",
            "password": "wrong_password",
        }

    @staticmethod
    def empty_username() -> dict:
        """
        Returns credentials with an empty username.
        """
        return {
            "username": "",
            "password": "secret_sauce",
        }

    @staticmethod
    def empty_password() -> dict:
        """
        Returns credentials with an empty password.
        """
        return {
            "username": "standard_user",
            "password": "",
        }

    @classmethod
    def custom(cls, overrides: dict) -> dict:
        """
        Generates custom user credentials with dynamic overrides.
        """
        logger.debug("Generating custom user credentials with overrides", {"overrides": overrides})
        user = cls.valid_standard_user()
        user.update(overrides)
        return user
pass
