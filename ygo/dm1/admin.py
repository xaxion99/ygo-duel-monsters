from django.contrib import admin
from .models import Card, Language, CardImage, CardInfo, Fusion, FusionMaterialGroup, CardCollection


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

@admin.register(Fusion)
class FusionAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "result_card")

class FusionMaterialGroupInline(admin.TabularInline):
    model = FusionMaterialGroup
    extra = 0

@admin.register(FusionMaterialGroup)
class FusionMaterialGroupAdmin(admin.ModelAdmin):
    list_display = ("fusion",)
    filter_horizontal = ('material1', 'material2')

@admin.register(CardCollection)
class CardCollectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'card', 'card_number', 'quantity')
    search_fields = ('user__username', 'card__card_name',)

    def card_number(self, obj):
        return obj.card.card_info.number
    card_number.admin_order_field = "card__card_info__number"
    card_number.short_description = "Card Number"
