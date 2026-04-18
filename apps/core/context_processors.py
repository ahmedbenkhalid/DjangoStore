from django.utils.translation import get_language


def language_info(request):
    """Returns the current language code for templates."""
    return {"LANGUAGE_CODE": get_language()}


def page_layout(request):
    """
    Context processor to determine page layout type.
    Returns has_sidebar boolean based on current URL path.
    """
    path = request.path
    
    # Pages that should display with sidebar
    sidebar_paths = [
        '/products/',
        '/categories/',
        '/cart/',
        '/orders/',
        '/profile/',
    ]
    
    has_sidebar = any(path.startswith(p) for p in sidebar_paths)
    
    return {'has_sidebar': has_sidebar}