from django import template

from zenofewords.models import Navigation

register = template.Library()


@register.inclusion_tag('zenofewords/tags/navigation.html', takes_context=True)
def navigation_tag(context, navigation_slug, subnav=False):
    path = context['request'].path
    return {
        'subnav': subnav,
        'current_url': path.replace('/', '').replace(navigation_slug, ''),
        'navigation': Navigation.objects.filter(slug=navigation_slug).first()
    }


@register.filter
def floor(value):
    return int(value)
