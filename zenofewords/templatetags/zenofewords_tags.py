from django import template

from zenofewords.models import Navigation

register = template.Library()


@register.inclusion_tag('zenofewords/tags/navigation.html')
def navigation_tag(navigation_slug, subnav=False):
    return {
        'subnav': subnav,
        'navigation': Navigation.objects.filter(slug=navigation_slug).first()
    }


@register.filter
def floor(value):
    return int(value)
