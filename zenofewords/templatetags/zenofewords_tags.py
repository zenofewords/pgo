from django import template

from pgo.utils import NAVIGATION_ITEMS

register = template.Library()


@register.inclusion_tag('zenofewords/tags/navigation.html', takes_context=True)
def navigation_tag(context):
    return {
        'current_url': context['request'].path,
        'navigation': NAVIGATION_ITEMS,
    }


@register.simple_tag
def is_active(current_url, key, first_item):
    if (first_item and current_url == '/') or key in current_url:
        return 'class=active'
    return ''


@register.filter
def format_stat_product(value):
    return '{}k'.format(str(value / 1000).split('.')[0])
