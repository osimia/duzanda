from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """Split the string by delimiter (default: comma)."""
    if not value:
        return []
    return [v.strip() for v in value.split(delimiter)]
