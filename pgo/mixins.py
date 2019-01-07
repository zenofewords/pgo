from django.views.generic.list import ListView


class ListViewOrderingMixin(ListView):
    paginate_by = 220

    def get_ordering(self):
        default = self.default_ordering
        ordering = self.request.GET.get('ordering', None)

        if ordering and ordering.replace('-', '') in self.ordering_fields:
            return ordering
        return default

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ordering'] = self.get_ordering()
        return context
