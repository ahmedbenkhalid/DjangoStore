"""
Custom middleware for the SmartS3R project.
"""

from django.utils.translation import get_language
from django.shortcuts import render

class HtmxPartialMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        if request.htmx and not request.htmx.boosted:
            # If it's an HTMX request but NOT a boosted link, we might want to return only the block
            # However, for SPA behavior with hx-boost, we usually want the whole page
            # But if we use hx-get explicitly, we might want a partial.
            # For now, let's focus on hx-boost which handles the swap automatically.
            pass
        return response

