import logging

from django.utils.translation import get_language

logger = logging.getLogger(__name__)


class LanguageCodeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = get_language()
        request.LANGUAGE_CODE = lang
        logger.debug(f"LanguageCodeMiddleware: path={request.path}, lang={lang}")
        return self.get_response(request)