import factory

from django.contrib.auth import get_user_model


class UserFactory(factory.django.DjangoModelFactory):
    first_name = factory.Sequence(lambda n: 'first_name%s' % n)
    last_name = factory.Sequence(lambda n: 'last_name%s' % n)
    username = factory.Sequence(lambda n: 'username%s' % n)
    email = factory.LazyAttribute(lambda o: '%s@example.com' % o.first_name)

    class Meta:
        model = get_user_model()


class AdminUserFactory(UserFactory):
    is_staff = True
    is_superuser = True
