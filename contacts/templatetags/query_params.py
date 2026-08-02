"""Template tag for building URLs that preserve the current query string."""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_with(context, **kwargs):
    """Return the current query string with the given parameters replaced.

    Used by pagination links so that search and sort survive page changes.
    """
    params = context["request"].GET.copy()
    for key, value in kwargs.items():
        params[key] = value
    return f"?{params.urlencode()}"
