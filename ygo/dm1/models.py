from django.contrib.auth.models import User
from django.db import models

class Card(models.Model):
    card_name = models.CharField("Card Name", max_length=255)

    def __str__(self):
        return self.card_name


class Language(models.Model):
    card = models.OneToOneField(Card, on_delete=models.CASCADE, related_name="language", null=True, blank=True)
    japanese = models.CharField("Japanese", max_length=255)
    romaaji = models.CharField("Rōmaji", max_length=255)
    translated = models.CharField("Translated", max_length=255)

    def __str__(self):
        return self.translated


class CardImage(models.Model):
    card = models.OneToOneField(Card, on_delete=models.CASCADE, related_name="card_image", null=True, blank=True)
    src = models.URLField("Image URL")
    alt = models.CharField("Alt Text", max_length=255)
    width = models.PositiveIntegerField("Width")
    height = models.PositiveIntegerField("Height")
    data_file_width = models.PositiveIntegerField("Data File Width")
    data_file_height = models.PositiveIntegerField("Data File Height")

    def __str__(self):
        return self.alt


class CardInfo(models.Model):
    card = models.OneToOneField(Card, on_delete=models.CASCADE, related_name="card_info", null=True, blank=True)
    number = models.PositiveIntegerField("Number")
    atk_def = models.CharField("ATK/DEF", max_length=50)
    card_type = models.CharField("Type", max_length=50)
    rarity = models.CharField("Rarity", max_length=10)
    lore = models.TextField("Lore")

    def __str__(self):
        return f"{self.number} - {self.rarity}"


class Fusion(models.Model):
    number = models.PositiveIntegerField("Fusion Number")
    name = models.CharField("Fusion Name", max_length=255)
    result_card = models.ForeignKey(
        Card,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fusion_result",
        verbose_name="Fusion Result Card"
    )

    def __str__(self):
        return f"{self.number}: {self.name}"


class FusionMaterialGroup(models.Model):
    fusion = models.ForeignKey(
        Fusion,
        on_delete=models.CASCADE,
        related_name="material_groups",
        verbose_name="Fusion Recipe"
    )
    # Each group can have one or more cards on each side.
    material1 = models.ManyToManyField(
        Card,
        related_name="fusion_material1",
        verbose_name="Material 1 Cards",
        blank=True
    )
    material2 = models.ManyToManyField(
        Card,
        related_name="fusion_material2",
        verbose_name="Material 2 Cards",
        blank=True
    )

    def __str__(self):
        m1 = ", ".join(card.card_name for card in self.material1.all())
        m2 = ", ".join(card.card_name for card in self.material2.all())
        return f"{self.fusion} | Material1: {m1} | Material2: {m2}"


class CardCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='card_collection')
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='collection_entry', verbose_name="Card")
    quantity = models.PositiveIntegerField("Quantity Owned", default=0, help_text="Number of this card owned.")

    class Meta:
        unique_together = ('user', 'card')

    def __str__(self):
        return f"{self.card.card_name}: {self.quantity}"