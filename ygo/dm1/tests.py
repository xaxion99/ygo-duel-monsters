# dm1/tests.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Card, CardInfo, CardCollection, Fusion, FusionMaterialGroup

User = get_user_model()


class DeckFusionCalculatorTest(TestCase):
    def setUp(self):
        # Create a test user.
        self.user = User.objects.create_user(username='testuser', password='password')

        # Create some cards and their associated CardInfo.
        self.card1 = Card.objects.create(card_name="Card1")
        CardInfo.objects.create(card=self.card1, number=1, atk_def="1000 / 2000", card_type="Dragon", rarity="R",
                                lore="...")

        self.card2 = Card.objects.create(card_name="Card2")
        CardInfo.objects.create(card=self.card2, number=2, atk_def="1500 / 1000", card_type="Spellcaster", rarity="R",
                                lore="...")

        self.card3 = Card.objects.create(card_name="Card3")
        CardInfo.objects.create(card=self.card3, number=3, atk_def="2000 / 1500", card_type="Warrior", rarity="R",
                                lore="...")

        self.card4 = Card.objects.create(card_name="Card4")
        CardInfo.objects.create(card=self.card4, number=4, atk_def="2500 / 1500", card_type="Warrior", rarity="R",
                                lore="...")

        # Create CardCollection entries (user owns all these cards).
        CardCollection.objects.create(user=self.user, card=self.card1, quantity=1)
        CardCollection.objects.create(user=self.user, card=self.card2, quantity=1)
        CardCollection.objects.create(user=self.user, card=self.card3, quantity=1)
        CardCollection.objects.create(user=self.user, card=self.card4, quantity=1)

        # Create Fusion A (primary fusion) where:
        # - result_card is card3.
        # - materials: material1 is card1 and material2 is card2.
        self.fusionA = Fusion.objects.create(number=10, name="FusionA", result_card=self.card3)
        groupA = FusionMaterialGroup.objects.create(fusion=self.fusionA)
        groupA.material1.add(self.card1)
        groupA.material2.add(self.card2)

        # Create Fusion B (secondary fusion scenario) where:
        # - result_card is card4.
        # - materials: material1 is card3 and material2 is card2.
        # Here, card3 is a fusion result (from FusionA) and is owned, so it appears in owned_result_cards.
        self.fusionB = Fusion.objects.create(number=20, name="FusionB", result_card=self.card4)
        groupB = FusionMaterialGroup.objects.create(fusion=self.fusionB)
        groupB.material1.add(self.card3)
        groupB.material2.add(self.card2)

    def test_deck_fusion_calculator_secondary_fusions(self):
        # Log in as the test user.
        self.client.login(username='testuser', password='password')
        url = reverse('deck_fusion_calculator')

        # Request the deck fusion calculator view with the filter set to "owned".
        response = self.client.get(url, {'filter': 'owned'})
        self.assertEqual(response.status_code, 200)

        # Retrieve the secondary fusions from the context.
        secondary_possible_fusions = response.context['secondary_possible_fusions']

        # We expect one secondary fusion (from FusionB) based on our test data.
        self.assertEqual(len(secondary_possible_fusions), 1)
