"""
URL configuration for lab3 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from events_app import views 
from django.urls import include, path
from rest_framework import routers

urlpatterns = [
    path('admin/', admin.site.urls),
    path(r'events/', views.EventsList.as_view(), name='events-list'),                         # список угроз (GET)
    path(r'events/<int:pk>/', views.EventDetail.as_view(), name='event-detail'),             # детальное описание мероприятия (GET), изменение (PUT), удаление (DELETE)
    path(r'events/create/', views.EventDetail.as_view(), name='events-create'),                     # добавление (POST), 
    path(r'events/delete/<int:pk>/', views.EventDetail.as_view(), name='events-delete'), 
    path(r'events/signup/', views.AddEventView.as_view(), name='add-event-to-visit'), # добавление в заявку для пользователя
    path(r'events/image/', views.ImageView.as_view(), name='add-image'),             # замена изображения

    path(r'list-visits/',views.ListVisits.as_view(),name='list-visits-by-username'),
    path(r'visit/<int:pk>/',views.GetVisits.as_view(),name='get-visit-by-id'),
    path(r'visit/<int:pk>/',views.GetVisits.as_view(),name='put-visit-by-id'),
    path(r'form-visit/<int:pk>/',views.FormVisit.as_view(),name='form-visit-by-id'),
    path(r'moderate-visit/<int:pk>/',views.ModerateVisit.as_view(),name='moderate-visit-by-id'),
    path(r'delete-visit/<int:pk>/',views.ModerateVisit.as_view(),name='delete-visit-by-id'),

    path(r'delete-event-visit/<int:pk>/',views.EditRequestThreat.as_view(),name='delete-event-from-visit'),
    path(r'edit-event-visit/<int:pk>/',views.EditRequestThreat.as_view(),name='edit-event-in-visit'),

    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('profile/', views.UserUpdateView.as_view(), name='profile'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
]
