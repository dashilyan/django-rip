from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from .serializers import *
from .models import Visit, Event, EventVisit
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import logout, login, authenticate
from datetime import datetime, timezone
import random
import redis
import uuid
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening
    
class EventsList(APIView):
    model_class = Event
    serializer_class = EventsListSerializer

    @swagger_auto_schema(
        operation_description="Получение списка событий (можно фильтровать по типу события через параметр 'event_type')",
        responses={200: EventsListSerializer(many=True)}
    )
    
    def get(self, request):
        # if 'event_type' in request.GET:
        #     events=self.model_class.objects.filter(event_type__icontains=request.GET['event_type'])
        # else:
        #     events = self.model_class.objects.all()

        # serializer = self.serializer_class(events, many=True)
        # resp = serializer.data
        # draft_visit = False

        # if request.user.is_authenticated:
        #     draft_visit = Visit.objects.filter(user=request.user, status='draft')

        # if draft_visit:
        #     request_serializer = EventsListSerializer(draft_visit)  # Use RequestSerializer here
        #     resp.append({'visit': request_serializer.data})
        # else:
        #     resp.append({'visit':{'pk':None,'events_count':0}})

        # return Response(resp,status=status.HTTP_200_OK)

        if 'event_type' in request.GET:
            events=self.model_class.objects.filter(event_type__icontains=request.GET['event_type'])
        else:
            events = self.model_class.objects.all()

        serializer = self.serializer_class(events, many=True)
        resp = serializer.data
        draft_visit = False
        
        # if not request.user is None:
        #     draft_visit = Visit.objects.get(user=request.user, status='draft')
        if request.user and request.user.is_authenticated:
            try:
                draft_visit = Visit.objects.get(user=request.user, status='draft')
            except Exception:
                pass
        if draft_visit:
            request_serializer = VisitSerializerInList(draft_visit)
            resp.append({'visit': request_serializer.data})
        else:
            resp.append({'visit': None, 'events_count': 0})

        return Response(resp, status=status.HTTP_200_OK)


class EventDetail(APIView):
    model_class = Event
    serializer_class = EventDetailSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    @swagger_auto_schema(
        operation_description="Получение детальной информации о событии по ID",
        responses={200: EventDetailSerializer}
    )
    def get(self, request, pk):
        event = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(event)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Удаление события по ID",
        responses={204: "No Content"}
    )
    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        event = get_object_or_404(self.model_class, pk=pk)
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @csrf_exempt
    @swagger_auto_schema(
        request_body=EventDetailSerializer,
        operation_description="Создание нового события",
        responses={201: EventDetailSerializer, 400: "Bad Request"}
    )
    def post(self, request):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
         
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        request_body=EventDetailSerializer,
        operation_description="Обновление события (частично)",
        responses={200: EventDetailSerializer, 400: "Bad Request"}
    )
    def put(self, request, pk):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
         
        event = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddEventView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes=[IsAuthenticated]

    @csrf_exempt
    @swagger_auto_schema(
        request_body=EventVisitSerializer,
        operation_description="Добавление события в черновой визит пользователя",
        responses={200: "OK", 400: "Bad Request"}
    )

    def post(self, request, pk):
        # создаем заявку, если ее еще нет
        if not Visit.objects.filter(user=request.user,status='draft').exists():
            new_req = Visit()
            new_req.user = request.user
            new_req.save()
            
        # получаем id заявки
        visit_id = Visit.objects.filter(user=request.user,status='draft').first().pk
        if Event.objects.filter(pk=pk).exists():
            if (EventVisit.objects.filter(event_id=pk,visit_id=visit_id).exists()):
                return Response({'error':'Событие уже добавлено в заявку'}, status=status.HTTP_200_OK)
            
            # event = Event.objects.get(pk=pk)
            new_event_visit = EventVisit()
            new_event_visit.event_id = pk
            new_event_visit.visit_id = visit_id

            if 'date' in request.data:
                new_event_visit.date = request.data["date"]
            new_event_visit.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response({'error':'event not found'}, status=status.HTTP_404_NOT_FOUND)


class ImageView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    def process_file_upload(self, file_object: InMemoryUploadedFile, client, image_name):
        try:
            client.put_object('static', image_name, file_object, file_object.size)
            return f"http://192.168.56.101:9000/static/{image_name}"
        except Exception as e:
            return {"error": str(e)}

    def add_pic(self, event, pic):
        client = Minio(
            endpoint=settings.AWS_S3_ENDPOINT_URL,
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            secure=settings.MINIO_USE_SSL
        )
        i = event.id
        img_obj_name = f"{i}.png"

        if not pic:
            return Response({"error": "Нет файла для изображения логотипа."})
        result = self.process_file_upload(pic, client, img_obj_name)

        if 'error' in result:
            return Response(result)

        event.img_url = result
        event.save()

        return Response({"message": "success"})
    
    @csrf_exempt
    @swagger_auto_schema(
        request_body=AddImageSerializer,
        operation_description="Загрузка изображения для события",
        responses={201: "Image uploaded successfully", 400: "Bad Request"}
    )
    def post(self, request):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        serializer = AddImageSerializer(data=request.data)
        if serializer.is_valid():
            event = Event.objects.get(pk=serializer.validated_data['event_id'])
            pic = request.FILES.get("pic")
            img_result = self.add_pic(event, pic)
            if 'error' in img_result.data:
                return img_result
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListVisits(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    @swagger_auto_schema(
        operation_description="Получение списка всех визитов, кроме черновиков",
        responses={200: VisitSerializer(many=True)}
    )
    def get(self, request):

        visits = Visit.objects.exclude(status='deleted')
        if 'start_date' in request.GET:
            visits = visits.filter(formed_at__gte=request.GET['start_date'])
        if 'end_date' in request.GET:
            visits = visits.filter(formed_at__lte=request.GET['end_date'])
        if 'status' in request.GET:
            visits = visits.filter(status=request.GET['status'])

        if request.user.is_staff:
            visits = visits.exclude(status='draft')

        visit_serializer = VisitSerializer(visits,many=True)
        return Response(visit_serializer.data,status=status.HTTP_200_OK)

class GetVisits(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Получение деталей визита по ID",
        responses={200: VisitSerializer}
    )
    def get(self, request, pk):
        req = get_object_or_404(Visit, pk=pk)
        events_visits = EventVisit.objects.filter(visit=req)

        events = [event_visit.event for event_visit in events_visits]
        events_serializer = EventsInVisitSerializer(events, many=True, context={'visit_id':pk})
        visit_serializer = VisitSerializer(req)

        response = visit_serializer.data
        response['events'] = events_serializer.data

        return Response(response, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=PutVisitSerializer,
        operation_description="Обновление визита",
        responses={200: "Visit updated", 400: "Bad Request"}
    )
    def put(self, request, pk):
        serializer = PutVisitSerializer(data=request.data)
        if serializer.is_valid():
            req = get_object_or_404(Visit, pk=pk)
            for attr, value in serializer.validated_data.items():
                setattr(req, attr, value)
            req.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FormVisit(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes=[IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Формирование чернового визита",
        responses={200: "Visit formed", 400: "Bad Request"}
    )
    def put(self, request, pk):

        req = get_object_or_404(Visit, pk=pk)
        if not req.status == 'draft':
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        if not request.user == req.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        if req.created_at > datetime.now(timezone.utc):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if not req.ended_at == None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        req.formed_at = datetime.now(timezone.utc)
        req.status = 'formed'
        req.save()
        return Response(status=status.HTTP_200_OK)


class ModerateVisit(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    @swagger_auto_schema(
        request_body=AcceptVisitSerializer,
        operation_description="Модерация визита (принятие/отклонение)",
        responses={200: "Visit moderated", 400: "Bad Request"}
    )
    def put(self, request, pk):

        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        req = get_object_or_404(Visit, pk=pk)
        serializer = AcceptVisitSerializer(data=request.data)
        if not req.status == 'formed':
            return Response({'error': 'Заявка не сформирована'}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            if serializer.validated_data['accept'] == True and req.status:
                req.status = 'accepted'
                req.ended_at = datetime.now(timezone.utc)
                req.visitors = random.randint(1, 120)
            else:
                req.status = 'declined'
                req.ended_at = datetime.now(timezone.utc)
            req.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Удаление визита",
        responses={200: "Visit deleted"}
    )
    def delete(self, request, pk):
        req = get_object_or_404(Visit, pk=pk)
        req.status = 'deleted'
        req.ended_at = datetime.now()
        req.formed_at = None
        req.save()
        return Response(status=status.HTTP_200_OK)


class EditEventVisit(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'event_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE)
            }
        ),
        operation_description="Изменение даты или удаление события из визита",
        responses={200: "Visit updated", 400: "Bad Request"}
    )
    def put(self, request, pk):

        # if not request.user.is_staff:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        if 'event_id' in request.data and 'date' in request.data:
            record = get_object_or_404(EventVisit, visit=pk, event=request.data['event_id'])
            record.date = request.data['date']
            record.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'event_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        operation_description="Удаление события из визита",
        responses={200: "Visit updated", 400: "Bad Request"}
    )
    def delete(self, request, pk):

        if 'event_id' in request.data:
            record = get_object_or_404(EventVisit, visit=pk, event=request.data['event_id'])
            record.delete()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


# USER VIEWS

class UserRegistrationView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    @swagger_auto_schema(
        request_body=UserRegistrationSerializer,
        operation_description="Регистрация нового пользователя",
        responses={201: "User registered", 400: "Bad Request"}
    )
    @csrf_exempt
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    @swagger_auto_schema(
        request_body=UserUpdateSerializer,
        operation_description="Обновление данных пользователя",
        responses={200: "User updated", 400: "Bad Request"}
    )
    def put(self, request):
        serializer = UserUpdateSerializer(instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    @swagger_auto_schema(
        request_body=AuthTokenSerializer,
        operation_description="Вход пользователя",
        responses={200: "User logged in", 400: "Bad Request"}
    )
    @csrf_exempt
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)  # Создание сессионной аутентификации
                return Response({'message': 'User is logged successfully',"username":user.username,"is_staff":user.is_staff}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    
    permission_classes = [IsAuthenticated]
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    @csrf_exempt
    @swagger_auto_schema(
        operation_description="Logout the authenticated user.",
        responses={204: "Logout successful"}
    )
    
    def post(self, request):
        logout(request)  # Удаление сессии пользователя
        return Response(status=status.HTTP_204_NO_CONTENT)
