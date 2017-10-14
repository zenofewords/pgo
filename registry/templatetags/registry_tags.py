from django import template
from django.contrib.staticfiles.templatetags.staticfiles import static

register = template.Library()


@register.filter
def team_logo_url(team_slug):
    return static('static/images/team-{}-logo.png'.format(team_slug))
