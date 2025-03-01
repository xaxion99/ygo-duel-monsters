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
    number = models.CharField("Number", max_length=20)
    atk_def = models.CharField("ATK/DEF", max_length=50)
    card_type = models.CharField("Type", max_length=50)
    rarity = models.CharField("Rarity", max_length=10)
    lore = models.TextField("Lore")

    def __str__(self):
        return f"{self.number} - {self.rarity}"

