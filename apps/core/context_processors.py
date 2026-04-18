from django.utils.translation import get_language


def language_info(request):
    return {"LANGUAGE_CODE": get_language()}