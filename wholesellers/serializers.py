from rest_framework import serializers
from wholesellers.models import WholeSeller

# wholeseller serializer
class WholeSellerSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance.region = validated_data["region"]
        instance.points_earned = validated_data["points_earned"]
        instance.save()

        return instance

    class Meta:
        model = WholeSeller
        fields = "__all__"
