from django import template

register = template.Library()


@register.filter
def length_gt(value, arg):
    try:
        return len(value) > int(arg)
    except (TypeError, ValueError):
        return False


@register.filter
def length_gte(value, arg):
    try:
        return len(value) >= int(arg)
    except (TypeError, ValueError):
        return False


@register.filter
def to_string(value):
    return str(value)