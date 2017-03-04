from django.contrib import admin

from zenofewords.models import (
    Navigation,
    NavigationItem,
)


class NavigationAdmin(admin.ModelAdmin):
    fields = ('user', 'name', 'slug', 'active',)
    prepopulated_fields = {'slug': ('name',)}


class NavigationItemAdmin(admin.ModelAdmin):
    fields = ('user', 'navigation', 'name', 'slug', 'order', 'active',)
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Navigation, NavigationAdmin)
admin.site.register(NavigationItem, NavigationItemAdmin)
