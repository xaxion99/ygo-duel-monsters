from django.contrib import admin
from .models import Card, Language, CardImage, CardInfo

class LanguageInline(admin.StackedInline):
    model = Language
    extra = 0

class CardImageInline(admin.StackedInline):
    model = CardImage
    extra = 0

class CardInfoInline(admin.StackedInline):
    model = CardInfo
    extra = 0

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("id", "card_name")
    inlines = [LanguageInline, CardImageInline, CardInfoInline]
