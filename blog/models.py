from __future__ import unicode_literals

from django.db import models

from zenofewords.mixins import (
    DefaultModelMixin,
    SlugMixin,
)


class Blog(DefaultModelMixin, SlugMixin):
    title = models.CharField(max_length=300)
    content = models.TextField()

    def __str__(self):
        return self.title
