from django.contrib import admin
from .models import Review


class WordFilter(admin.SimpleListFilter):

    title = "Filter by words!"
    parameter_name = "word"

    def lookups(self, request, model_admin):
        return [
            ("good", "Good"),
            ("bad", "Bad"),
        ]

    def queryset(self, request, reviews):
        word = self.value()
        match = {
            "good": reviews.filter(rating__gte=3),
            "bad": reviews.filter(rating__lt=3),
        }
        return match.get(word, reviews)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = (
        "__str__",
        "payload",
    )
    list_filter = (
        WordFilter,
        "rating",
        "user__is_host",
        "room__category",
        "room__pet_friendly",
    )
