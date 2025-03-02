from django import template

register = template.Library()

@register.filter(name='trim')
def trim(value):
    """Trims leading and trailing whitespace from a string."""
    try:
        return value.strip()
    except AttributeError:
        return value
