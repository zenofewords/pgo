from django import template

from zenofewords.models import Navigation

register = template.Library()


@register.inclusion_tag('zenofewords/tags/navigation.html')
def navigation_tag(navigation_slug):
    return {
        'menu_items': Navigation.objects.get(slug=navigation_slug)
    }
