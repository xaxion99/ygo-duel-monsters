import json
from django.core.management.base import BaseCommand
from dm1.models import Card, Language, CardImage, CardInfo

class Command(BaseCommand):
    help = "Load cards from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="The JSON file to import")

    def handle(self, *args, **options):
        json_file = options["json_file"]
        with open(json_file, encoding="utf-8") as f:
            cards_data = json.load(f)

        for card_obj in cards_data:
            fields = card_obj.get("fields", {})

            # Create the Card instance first
            card = Card.objects.create(
                card_name=fields.get("card_name", "")
            )

            # Create the Language instance, linking it to the Card
            lang_data = fields.get("languages", {})
            Language.objects.create(
                card=card,
                japanese=lang_data.get("Japanese", ""),
                romaaji=lang_data.get("Rōmaji", ""),
                translated=lang_data.get("Translated", "")
            )

            # Create the CardImage instance, linking it to the Card
            img_data = fields.get("image", {})
            CardImage.objects.create(
                card=card,
                src=img_data.get("src", ""),
                alt=img_data.get("alt", ""),
                width=int(img_data.get("width", 0)),
                height=int(img_data.get("height", 0)),
                data_file_width=int(img_data.get("data_file_width", 0)),
                data_file_height=int(img_data.get("data_file_height", 0))
            )

            # Create the CardInfo instance, linking it to the Card
            info_data = fields.get("info", {})
            CardInfo.objects.create(
                card=card,
                number=info_data.get("Number", ""),
                atk_def=info_data.get("ATK/DEF", ""),
                card_type=info_data.get("Type", ""),
                rarity=info_data.get("Rarity", ""),
                lore=info_data.get("lore", "")
            )

            self.stdout.write(self.style.SUCCESS(f"Loaded card: {fields.get('card_name', 'Unknown')}"))

        self.stdout.write(self.style.SUCCESS("All cards loaded successfully."))
