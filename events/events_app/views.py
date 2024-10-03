from django.shortcuts import render
from .models import *
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.db import connection

# Create your views here.
# EVENTS = [{'id':1,'name':'Русская система обучения ремеслам','duration':'3 ч.','description':'На конференции выступят авторы пятого альманаха "Русская система обучения ремеслам. Истоки и традиции", изданного в формате pdf. Г.Б. Ефимов, старший научный сотрудник Института прикладной математики им. М.В. Келдыша РАН. Правнук А.В. Бари, выступая с докладом, приведут много интереснейших примеров из жизни своего выдающегося предка, строившего Россию вместе с В.Г. Шуховым. Например, он серьезно занимался благотворительностью - поддерживал рекламой издания Политехнического общества ИМТУ, помогал людям, попавшим в беду. ','type':'Конференция','img_url':'http://192.168.1.26:9000/static/6conf.jpg'},
#           {'id':2,'name':'Для детей','duration':'1,5 ч.','description':'Экскурсия для детей в музее вуза - это увлекательное путешествие по истории и достижениям университета. Дети познакомятся с уникальными экспонатами, артефактами и лабораториями, узнают о знаменитых выпускниках и преподавателях вуза. На экскурсии будут проведены интересные игры, мастер-классы и развивающие задания, которые помогут детям узнать больше о мире науки и образования. Это отличная возможность для детей расширить свои знания и вдохновиться научными открытиями.','type':'Экскурсия','img_url':'http://192.168.1.25:9000/static/children.jpg'},
#           {'id':3,'name':'Диалог поколений','duration':'1,5 ч.','description':'20 февраля 2019 года профком работников и Совет ветеранов МГТУ им. Н. Э. Баумана провели в музее Университета встречу с ветеранами войны и труда. На встрече будут профессор Добряков А.А., пенсионеры Кокарева М.Н., Шмакова Т.Н., Вереина Л.И., инженер НТБ Грецкий В.В., доцент Ореховский А. В. В этом году встреча посвящена 75-й годовщине прорыва блокады Ленинграда и победе в Сталинградской битве. Традиционно на встрече выступили ветераны с воспоминаниями и студенты с тематическими номерами. Студенты факультета МТ подготовили концертную программу: песни исполнили Золотарев Владимир, Костанянц Андрей и Гаврилова Екатерина. Выступления профессора Добрякова А. А. и доцента Ореховского А.В. напомнили о мужестве и героизме защитников Родины. Тронули до слёз стихи в исполнении внуков Ореховского А. В. − Ульяны и Дмитрия Чупахиных. С заключительным словом выступила председатель профкома Барышникова О.О. Ветераны тепло пообщались с молодежью. В неформальной обстановке наши ветераны выпью чаю и исполнили песни военных лет.','type':'Встреча','img_url':'http://192.168.1.25:9000/static/roundtable.jpg'},
#           {'id':4,'name':'Гриневецкий В. И.','duration':'45 мин.','description':'Василий Игнатьевич Гриневецкий сыграл выдающуюся роль в развитии отечественного инженерного образования, промышленности, энергетики, экономики. Его коллегами или учениками были такие выдающиеся люди, как аэродинамик и механик Н.Е. Жуковский, механик П.К. Худяков, крупнейший электротехник, организатор МЭИ К. А. Круг, гидродинамик А. И. Астров, механик И.А. Калинников, теплотехники Л. К. Рамзин, Н. Р. Брилинг, Е. К. Мазинг и многие другие деятели науки и техники. Как писал в 1922 году его ученик Э.А. Сатель «…Гриневецкий своим широким умом, своими разносторонними знаниями, обаянием своей личности предназначен был стоять во главе инженерной среды, давать основные направляющие линии в той технико-экономической работе воссоздания русской промышленности..». Глубокий мыслитель, блестящий лектор, опытный инженер, образованный экономист, энергичный администратор, человек с блестящей интуицией – вот какие черты помогли В.И. Гриневецкому консолидировать знаменитую московскую школу теплотехников, на базе которой впоследствии его учениками был создан Всесоюзный теплотехнический институт, быть флагманом инженерного политехнического образования в труднейшие годы первой мировой и гражданской войн. 13 июля 1921 года Совет Труда и Обороны постановил: «В воздаяние заслуг и увековечения памяти основателей и главных руководителей Московской школы теплотехников учредить теплотехнический институт, присвоив ему наименование «Теплотехнический институт имени профессоров В.И. Гриневецкого и К.В. Кирша».','type':'Выставка','img_url':'http://192.168.1.25:9000/static/grinevetsky.jpg'},
#           {'id':5,'name':'Для 1 курса','duration':'1,5 ч.','description':'Экскурсия для первого курса в музее вуза - это увлекательное и познавательное мероприятие, которое позволит новичкам познакомиться с историей и традициями своего учебного заведения. Во время экскурсии студенты смогут узнать об ученых, выпускниках и достижениях вуза, ознакомиться с уникальными экспонатами из музейных коллекций и познакомиться с интересными фактами из прошлого университета. Это будет отличная возможность для первокурсников лучше узнать свою учебную среду, создать новые знакомства и провести время весело и с пользой. В конце экскурсии студенты смогут задать вопросы экскурсоводу и поговорить о том, что они узнали и увидели. Экскурсия в музее вуза станет незабываемым опытом для студентов первых курсов, который поможет им лучше погрузиться в атмосферу учебы и начать свой путь в новой образовательной среде.','type':'Экскурсия','img_url':'http://192.168.1.25:9000/static/museum.jpg'},
#           {'id':6,'name':'День студентов','duration':'1 ч.','description':'В праздничный для всех студентов, в музее МГТУ им. Н.Э. Баумана представители клуба Императорского технического училища торжественно вручат стипендии клуба. 50 студентов станут стипендиатами клуба. Они прошли суровый отбор: на стипендию претендовали 127 человек. Разовую (поощрительную) стипендию получат 41 студент. Годовую – пять студентов. Полугодовую (до завершения учебы в университете) получат четверо. Стипендии, дипломы и памятные подарки вручит президент клуба ИТУ Анатолий Долголаптев.','type':'Встреча','img_url':'http://192.168.1.25:9000/static/students-day.jpg'}]

# VISITS = [{'id':1,'group':'iu5-51b','events':[{'id':1,'name':'Русская система обучения ремеслам','event_date':'01.01.25'},
#                                                                   {'id':2,'name':'Для детей','event_date':'22.12.24'}]}]


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
     
    if 'event_name' in request.GET:
        for event in events:
            if request.GET['event_name'].lower() in event.event_name.lower():
                filtered_events.append(event)
        return render(request, 'index.html', {'events': filtered_events, 'input_value':request.GET['event_name'],'cart_count':cart_count,'visit_id':visit_id})
    
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
    # visit_id = request.POST.get('visit_id')
    with connection.cursor() as cursor:
        cursor.execute("UPDATE visits SET status = %s WHERE id = %s", ['deleted', id])
    return redirect('/')