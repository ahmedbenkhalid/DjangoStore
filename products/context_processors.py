from django.core.cache import cache
from .models import Category


def menu_categories(request):
    categories = cache.get("menu_categories")
    if categories is None:
        categories = list(Category.objects.all()[:10])
        cache.set("menu_categories", categories, 3600)

    count = cache.get("category_count")
    if count is None:
        count = Category.objects.count()
        cache.set("category_count", count, 3600)

    return {"menu_categories": categories, "has_more_categories": count > 10}
