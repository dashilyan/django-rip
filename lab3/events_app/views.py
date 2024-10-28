from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from .serializers import *
from .models import Visit, Event, EventVisit
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import logout
from datetime import datetime, timezone

from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile

class EventsList(APIView):
    model_class = Event
    serializer_class = EventsListSerializer

    # получить список мероприятий
    def get(self, request):
        if 'event_type' in request.GET:
            events=self.model_class.objects.filter(event_type = request.GET['event_type'])
        else:
            events = self.model_class.objects.all()

        serializer = self.serializer_class(events, many=True)
        resp = serializer.data
        draft_visit = Visit.objects.filter(user=1, status='draft').first()
        if draft_visit:
            request_serializer = VisitSerializerInList(draft_visit) 
            resp.append({'visit': request_serializer.data})
        else:
            resp.append({'visit': None})

        return Response(resp,status=status.HTTP_200_OK)

class EventDetail(APIView):
    model_class = Event
    serializer_class = EventDetailSerializer

    # получить описание мероприятия
    def get(self, request, pk):
        event = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(event)
        return Response(serializer.data)
    

    # удалить мероприятие (для модератора)
    def delete(self, request, pk):

        # if not 1.is_staff:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        event = get_object_or_404(self.model_class, pk=pk)
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    # добавить новую мероприятие (для модератора)
    def post(self, request, format=None):

        #if not 1.is_staff:
        #    return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # обновление мероприятия (для модератора)
    def put(self, request, pk, format=None):

        # if not 1.is_staff:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        event = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 

class AddEventView(APIView):
    # добавление услуги в заявку
    def post(self, request):
        # создаем заявку, если ее еще нет
        if not Visit.objects.filter(user=1,status='draft').exists():
            new_visit = Visit()
            new_visit.user = 1
            new_visit.save()
            
        visit_id = Visit.objects.filter(user=1,status='draft').first().pk
        serializer = EventVisitSerializer(data=request.data)
        if serializer.is_valid():
            new_visit_event = EventVisit()
            new_visit_event.event_id = serializer.validated_data["event_id"]
            new_visit_event.visit_id = visit_id
            if 'date' in request.data:
                new_visit_event.date = request.data["date"]
            new_visit_event.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


class ImageView(APIView):
    
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

    def post(self, request):
        #if not 1.is_staff:
        #    return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = AddImageSerializer(data=request.data)
        if serializer.is_valid():
            event = Event.objects.get(pk=serializer.validated_data['event_id'])
            pic = request.FILES.get("pic")
            img_result = self.add_pic(event, pic)
            # Если в результате вызова add_pic результат - ошибка, возвращаем его.
            if 'error' in img_result.data:    
                return img_result
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListVisits(APIView):
    def get(self, request):
        if 'date' in request.GET and 'status' in request.GET:
            requests = Visit.objects.filter(formed_at__gte=request.GET['date'],status=request.GET['status'])
        else:
            requests = Visit.objects.all()
        
        req_serializer = VisitSerializer(requests,many=True)
        return Response(req_serializer.data,status=status.HTTP_200_OK)

class GetVisits(APIView):
    
    def get(self, request, pk):
        req = get_object_or_404(Visit, pk=pk)
        serializer = VisitSerializer(req)

        events_visits = EventVisit.objects.filter(visit=req)
        events_ids = []
        for event_visit in events_visits:
            events_ids.append(event_visit.event_id)

        events_of_visit = []
        for id in events_ids:
            events_of_visit.append(get_object_or_404(Event,pk=id))

        events_serializer = EventsListSerializer(events_of_visit,many=True)
        response = serializer.data
        response['events'] = events_serializer.data

        return Response(response,status=status.HTTP_200_OK)
    
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
    def put(self, request, pk):
        req = get_object_or_404(Visit, pk=pk)
        if not req.status=='draft':
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if req.created_at > datetime.now(timezone.utc):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if not req.ended_at == None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        req.formed_at = datetime.now(timezone.utc)
        req.status = 'formed'
        req.save()
        return Response(status=status.HTTP_200_OK)
    

class ModerateVisit(APIView):
    def put(self,request,pk):
        req = get_object_or_404(Visit, pk=pk)
        serializer = AcceptRequestSerializer(data=request.data)
        if not req.status == 'formed':
            return Response({'error':'Заявка не сформирована'},status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            if serializer.validated_data['accept'] == True and req.status:
                req.status = 'accepted'
                # req.moderator = 1
                
            else:
                req.status = 'declined'
                # req.moderator = 1 
                req.ended_at = datetime.now(timezone.utc)
            req.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        

    def delete(self, request, pk):
        req = get_object_or_404(Visit, pk=pk)
        req.status = 'deleted'
        req.ended_at = datetime.now()
        req.save()
        return Response(status=status.HTTP_200_OK)
    

class EditRequestThreat(APIView):
    def delete(self, request, pk):
        if 'event_id' in request.data:
            record = get_object_or_404(EventVisit, visit=pk,event=request.data['event_id'])
            record.delete()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
    def put(self,request,pk):
        if 'event_id' in request.data and 'date' in request.data:
            record = get_object_or_404(EventVisit, visit=pk,event=request.data['event_id'])
            record.date = request.data['date']
            record.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


# USER VIEWS
class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# Личный кабинет (обновление профиля)
class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = UserUpdateSerializer(instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Аутентификация пользователя
class UserLoginView(APIView):
    def post(self, request):
        serializer = AuthTokenSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Деавторизация пользователя
class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()  # Удаляем токен
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)