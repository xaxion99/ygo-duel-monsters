from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    """
    Splits the string 'value' by the given 'delimiter' and returns a list.
    """
    try:
        return value.split(delimiter)
    except Exception:
        return []
