import factory.fuzzy
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.fuzzy.FuzzyText(length=12)
    is_superuser = True


class TokenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Token

    user = factory.SubFactory(UserFactory)
