from rest_framework import serializers

import datetime as dt

from rest_framework.validators import UniqueTogetherValidator

from .models import CHOICES, Achievement, AchievementCat, Cat, User


class UserSerializer(serializers.ModelSerializer):
    cats = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'cats')
        ref_name = 'ReadOnlyUsers'


class AchievementSerializer(serializers.ModelSerializer):
    achievement_name = serializers.CharField(source='name')

    class Meta:
        model = Achievement
        fields = ('id', 'achievement_name')


class CatSerializer(serializers.ModelSerializer):
    achievements = AchievementSerializer(read_only=True, many=True)
    color = serializers.ChoiceField(choices=CHOICES)
    age = serializers.SerializerMethodField()
    owner = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = Cat
        fields = ('id', 'name', 'color', 'birth_year', 'achievements',
                  'owner', 'age')
        validators = [
            UniqueTogetherValidator(
                queryset=Cat.objects.all(),
                fields=('name', 'owner')
            )
        ]

    @staticmethod
    def validate_birth_year(value):
        year = dt.date.today().year
        if not (year - 40 < value <= year):
            raise serializers.ValidationError('Проверьте год рождения!')
        return value

    @staticmethod
    def get_age(obj):
        return dt.datetime.now().year - obj.birth_year

    def validate(self, data):
        if data['color'] == data['name']:
            raise serializers.ValidationError(
                'Имя не может совпадать с цветом!')
        return data

    def create(self, validated_data):
        if 'achievements' not in self.initial_data:
            cat = Cat.objects.create(**validated_data)
            return cat
        else:
            achievements = validated_data.pop('achievements')
            cat = Cat.objects.create(**validated_data)
            for a in achievements:
                current_a, _ = Achievement.objects.get_or_create(**a)
                AchievementCat.objects.create(
                    achievement=current_a, cat=cat)
            return cat
