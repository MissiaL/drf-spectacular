import uuid
from unittest import mock

import pytest
from django.db import models
from rest_framework import serializers, viewsets, routers, mixins
from rest_framework.renderers import JSONRenderer

from drf_spectacular.openapi import SchemaGenerator, AutoSchema
from tests import assert_schema


class TreeNode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    label = models.TextField()

    parent = models.ForeignKey(
        'TreeNode',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.DO_NOTHING
    )


class TreeNodeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'label', 'parent', 'children']
        model = TreeNode

    def get_fields(self):
        fields = super(TreeNodeSerializer, self).get_fields()
        fields['children'] = TreeNodeSerializer(many=True)
        return fields


class TreeNodeViewset(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = TreeNodeSerializer
    queryset = TreeNode.objects.none()


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema)
def test_recursion(no_warnings):
    router = routers.SimpleRouter()
    router.register('nodes', TreeNodeViewset, basename="nodes")
    generator = SchemaGenerator(patterns=router.urls)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(schema, 'tests/test_recursion.yml')


@pytest.mark.skip
@pytest.mark.django_db
def test_model_setup_is_valid():
    root = TreeNode(label='root')
    root.save()
    leaf1 = TreeNode(label='leaf1', parent=root)
    leaf1.save()
    leaf2 = TreeNode(label='leaf2', parent=root)
    leaf2.save()

    JSONRenderer().render(
        TreeNodeSerializer(root).data,
        accepted_media_type='application/json; indent=4'
    ).decode()
