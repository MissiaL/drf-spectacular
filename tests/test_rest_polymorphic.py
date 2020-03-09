from unittest import mock

import pytest
from django.db import models
from polymorphic.models import PolymorphicModel
from rest_framework import viewsets, serializers, routers
from rest_framework.renderers import JSONRenderer
from rest_polymorphic.serializers import PolymorphicSerializer

from drf_spectacular.contrib.rest_polymorphic import PolymorphicAutoSchema
from drf_spectacular.openapi import SchemaGenerator
from tests import assert_schema, lazy_serializer


class Person(PolymorphicModel):
    address = models.CharField(max_length=30)


class LegalPerson(Person):
    company_name = models.CharField(max_length=30)
    board = models.ManyToManyField('Person', blank=True, null=True)


class NaturalPerson(Person):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)


class PersonSerializer(PolymorphicSerializer):
    model_serializer_mapping = {
        LegalPerson: lazy_serializer('tests.test_rest_polymorphic.LegalPersonSerializer'),
        NaturalPerson: lazy_serializer('tests.test_rest_polymorphic.NaturalPersonSerializer'),
    }


class LegalPersonSerializer(serializers.ModelSerializer):
    # notice that introduces a recursion loop
    board = PersonSerializer(many=True, read_only=True)

    class Meta:
        model = LegalPerson
        fields = ('id', 'company_name', 'address', 'board')


class NaturalPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturalPerson
        fields = ('id', 'first_name', 'last_name', 'address')


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', PolymorphicAutoSchema)
def test_polymorphic(no_warnings):
    router = routers.SimpleRouter()
    router.register('persons', PersonViewSet, basename="person")
    generator = SchemaGenerator(patterns=router.urls)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(schema, 'tests/test_rest_polymorphic.yml')


@pytest.mark.skip
@pytest.mark.django_db
def test_model_setup_is_valid():
    peter = NaturalPerson(first_name='Peter', last_name='Parker')
    peter.save()
    may = NaturalPerson(first_name='May', last_name='Parker')
    may.save()
    parker_inc = LegalPerson(company_name='Parker Inc', address='NYC')
    parker_inc.save()
    parker_inc.board.add(peter, may)

    spidey_corp = LegalPerson(company_name='Spidey Corp.', address='NYC')
    spidey_corp.save()
    spidey_corp.board.add(peter, parker_inc)

    output = JSONRenderer().render(
        PersonSerializer(spidey_corp).data,
        accepted_media_type='application/json; indent=4'
    ).decode()
    print(output)
