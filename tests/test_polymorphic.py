from unittest import mock

import pytest
from django.db import models
from rest_framework import viewsets, serializers, routers
from rest_framework.response import Response

from drf_spectacular.openapi import SchemaGenerator, AutoSchema
from drf_spectacular.utils import extend_schema, PolymorphicProxySerializer
from tests import assert_schema


class LegalPerson2(models.Model):
    company_name = models.CharField(max_length=30)


class NaturalPerson2(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)


class LegalPersonSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = LegalPerson2
        fields = ('id', 'company_name', 'type')

    def get_type(self) -> str:
        return 'LegalPerson'


class NaturalPersonSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = NaturalPerson2
        fields = ('id', 'first_name', 'last_name', 'type')

    def get_type(self) -> str:
        return 'NaturalPerson'


with mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema):
    class PersonViewSet(viewsets.GenericViewSet):
        @extend_schema(
            request=PolymorphicProxySerializer(
                component_name='MetaPerson',
                serializers=[LegalPersonSerializer, NaturalPersonSerializer],
                resource_type_field_name='type',
            ),
            responses=PolymorphicProxySerializer(
                component_name='MetaPerson',
                serializers=[LegalPersonSerializer, NaturalPersonSerializer],
                resource_type_field_name='type',
            )
        )
        def create(self, request, *args, **kwargs):
            return Response({})


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema)
def test_polymorphic(no_warnings):
    router = routers.SimpleRouter()
    router.register('persons', PersonViewSet, basename="person")
    generator = SchemaGenerator(patterns=router.urls)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(schema, 'tests/test_polymorphic.yml')


@pytest.mark.skip
@pytest.mark.django_db
def test_model_setup_is_valid():
    # TODO
    pass
