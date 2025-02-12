from django.db import models
from rest_framework import serializers


def get_id_serializer_for_model(
    model: type[models.Model],
) -> type[serializers.ModelSerializer]:
    """Return serializer for the given model with only `id` field."""

    class IdModelSerializer(serializers.ModelSerializer):

        class Meta:
            fields = (
                "id",
            )

    setattr(IdModelSerializer.Meta, "model", model)

    return IdModelSerializer
