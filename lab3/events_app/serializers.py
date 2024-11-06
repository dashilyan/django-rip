from .models import Event, Visit, EventVisit
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


class AddImageSerializer(serializers.Serializer):
    event_id = serializers.IntegerField(required=True)

    def validate(self, data):
        event_id = data.get('event_id')

        if not Event.objects.filter(pk=event_id).exists():
            raise serializers.ValidationError(f"event_id is incorrect")
        
        return data
class EventsInVisitSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ["pk", "event_name", "event_type", "duration", "img_url", "date"]

    def get_date(self, obj):
        event_visit = EventVisit.objects.filter(event=obj).first()
        return event_visit.date if event_visit else None
    
class VisitSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username') 
    moderator = serializers.CharField(source='moderator.username', allow_null=True)
    
    class Meta:
        model = Visit
        fields = ["pk","status","created_at","formed_at","ended_at","group","moderator","user","visitors"]
    
class VisitSerializerInList(serializers.ModelSerializer):
    events_count = serializers.SerializerMethodField()
    class Meta:
        model = Visit
        fields = ["pk","events_count"] 

    def get_events_count(self, obj):
        return EventVisit.objects.filter(visit_id=obj.pk).count()

class PutVisitSerializer(serializers.ModelSerializer): 
    class Meta:
        model = Visit
        fields = ["pk","status","created_at","formed_at","ended_at","group","moderator","user","visitors"]
        
class EventDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["pk","event_name","event_type","description","duration","img_url"]

class EventsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["pk","event_name","event_type","duration","img_url"]

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["pk","img_url"]

class EventVisitSerializer(serializers.Serializer):
    event_id = serializers.IntegerField(required=True)
   
    def validate(self, data):
        event_id = data.get('event_id')

        if not Event.objects.filter(pk=event_id).exists():
            raise serializers.ValidationError(f"event_id is incorrect")

        return data
    
class AcceptRequestSerializer(serializers.Serializer):
    accept = serializers.BooleanField()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class AuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user is None:
            raise serializers.ValidationError("Неверные учетные данные")
        return {'user': user}
    

class CheckUsernameSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate(self, data):
        if not User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Пользователь не существует")
        
        return data

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
