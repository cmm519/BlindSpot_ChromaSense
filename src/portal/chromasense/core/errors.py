"""Errors that use cases raise. Web API maps each one to a response."""


class CoreError(Exception):
    """Base class for errors that a use case reports to its caller."""


class InvalidImage(CoreError):
    """The uploaded file is unsupported or corrupted."""


class ImageNotFound(CoreError):
    """No stored image has this ID, or it has expired."""


class InvalidCoordinates(CoreError):
    """The point is outside the image."""


class NoEnhancementForProfile(CoreError):
    """The view needs a CVD type, and the profile has none."""


class AiUnavailable(CoreError):
    """The AI service cannot answer now."""


class AiRateLimited(CoreError):
    """A session or an IP address has made too many AI requests."""


class AiSpendCapReached(CoreError):
    """The global AI spend cap has been reached."""


class NotInterpreted(CoreError):
    """A question needs an interpretation of the image, and none exists."""
