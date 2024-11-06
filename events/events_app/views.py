from django.shortcuts import render
from .models import *
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.db import connection


def events_list(request):

    events = Event.objects.all()

    cart_count = 0

    visit_id = 1
    
    if Visit.objects.filter(status='draft').exists():
        visit = Visit.objects.get(status='draft')
        visit_id = visit.pk
        if EventVisit.objects.filter(visit=visit).exists():
            event_visit = EventVisit.objects.filter(visit=visit)
            cart_count = event_visit.count()

    filtered_events = []
     
    if 'event_type' in request.GET and request.GET['event_type']!='':
        filtered_events = Event.objects.filter(event_type__istartswith = request.GET['event_type'])
        return render(request, 'index.html', {'events': filtered_events, 'input_value':request.GET['event_type'],'cart_count':cart_count,'visit_id':visit_id})
    
    return render(request, 'index.html', {'events': events, 'cart_count':cart_count,'visit_id':visit_id})



def visit(request, id):
    if id == 0:
        return render(request, 'visit.html', {'current_visit':None})
    
    if Visit.objects.filter(id=id).exclude(status='draft').exists():
        return render(request, 'visit.html', {'current_visit':None})
    
    if not Visit.objects.filter(id=id).exists():
        return render(request, 'visit.html', {'current_visit':None})

    current_visit = Visit.objects.get(pk=id)

    events = []
    events_visits = EventVisit.objects.filter(visit=current_visit)
    for event_visit in events_visits:
        if Event.objects.filter(pk=event_visit.event.pk).exists():
            event = Event.objects.get(pk=event_visit.event.pk)
            vis = Visit.objects.get(pk=id)
            date = EventVisit.objects.get(event=event,visit=vis).date
            event.event_date = date
            events.append(event)

    current_visit.events = events

    return render(request, 'visit.html', {'current_visit': current_visit,'events':events})

def event_description(request, id):
    if Event.objects.filter(pk=id).exists():
        event = Event.objects.get(pk=id)
        return render(request, 'description.html', {'event':event})
    return render(request, 'description.html', {})


def add_event(request, id):

    if not Visit.objects.filter(status='draft').exists():
        visit = Visit()
        visit.group = 'ИУ5-51Б'
        visit.save()
    else:
        visit = get_object_or_404(Visit, status='draft')


    event = get_object_or_404(Event, pk=id)

    if EventVisit.objects.filter(visit=visit, event=event).exists():
        return redirect('/')

    event_visit = EventVisit()
    event_visit.date = '2024-10-31'
    event_visit.visit = visit
    event_visit.event = event
    event_visit.save()

    return redirect('/')

def del_visit(request,id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE visits SET status = %s WHERE id = %s", ['deleted', id])
    return redirect('/')