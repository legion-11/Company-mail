from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, get_object_or_404
from .forms import MessageForm
from .models import Message, Receivers
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils.timezone import activate, now
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import Count, Q
scheduler = BackgroundScheduler()
scheduler.start()


def just_send_mail(message):
    send_mail(message.title, message.text, message.sender, message.emails, fail_silently=False)


def send_mail_sheduled(message):
    if message.send_date:
        print('schedule add_b {}'.format(scheduler.get_jobs()))
        scheduler.pause()
        scheduler.add_job(func=just_send_mail, trigger='date',
                          run_date=message.send_date, args=[message], id=str(message.url))
        scheduler.resume()
        print('schedule add_a {}'.format(scheduler.get_jobs()))
    else:
        just_send_mail(message)


def del_shcedule(message):
    try:
        scheduler.remove_job(str(message.url))
    except:  # JobLookupError
        print('not found')


def search(request, page, messages, what_search):
    number_print = 30
    more = len(messages) > number_print * (page + 1)
    return render(request, 'mymail/search.html',
                  {"messages": messages[number_print * page: number_print * (page + 1)],
                   "next_page": page + 1,
                   "prev_page": page - 1,
                   "more": more, "what_search": what_search})


def search_received(request, page):
    activate('Europe/Kiev')
    if request.user.is_authenticated:
        current_user = request.user
        messages = Message.objects.filter(receivers__user=current_user, receivers__show=True) \
            .exclude(send_date__isnull=False, send_date__gt=datetime.datetime.now())\
            .order_by('-id')
        read = Receivers.objects.filter(message__in=messages, user=current_user).order_by('-message')
        messages = list(zip(messages, read))
        return search(request, page, messages, what_search='Received messages')
    else:
        return render(request, 'mymail/search.html', {'what_search': 'Received messages'})


def search_send(request, page):
    activate('Europe/Kiev')
    if request.user.is_authenticated:
        current_user = request.user
        messages = Message.objects.filter(sender=current_user, show=True).order_by('-id')

        print(messages)
        return search(request, page, messages, what_search='Send messages')
    else:
        return render(request, 'mymail/search.html', {'what_search': 'Send messages'})


def read_message(request, message_url):
    activate('Europe/Kiev')
    current_user = request.user
    try:
        message = Message.objects.get(url=str(message_url))
        receiver = message.receivers.filter(user=current_user)
        if current_user == message.sender:
            if message.send_date and message.send_date > now():
                initial_dict = {
                    "title": message.title,
                    "receivers": [r.user for r in message.receivers.all()],
                    "text": message.text,
                    "send_date": message.send_date,
                    "emails": message.emails
                }
                form = MessageForm(request.POST or None, initial=initial_dict)
                if request.method == "POST" and form.is_valid():
                    data = form.cleaned_data
                    message.title = data.get('title')
                    message.text = data.get('text')
                    message.send_date = data.get('send_date')
                    receivers_user = data.get('receivers')

                    to_delete = list(message.receivers.all().exclude(user__in=receivers_user))
                    ids=[r.user.id for r in message.receivers.all()]
                    to_add = list(receivers_user.exclude(id=current_user.id).exclude(id__in=ids))

                    for i in range(min(len(to_delete), len(to_add))):
                        r = to_delete.pop()
                        r.user = to_add.pop()
                        r.save()
                    for r in to_delete:
                        r.delete()
                    for u in to_add:
                        r = Receivers(user=u, message=message)
                        r.save()

                    if message.emails:
                        del_shcedule(message)
                    message.emails = data.get('emails')
                    if current_user in receivers_user:
                        message.show_template = True
                    message.save()

                    if message.emails:
                        send_mail_sheduled(message)

                    return redirect('send/0')
                return render(request, 'mymail/edit.html', locals())

        elif receiver:
            if not message.send_date or message.send_date < now():
                receiver = receiver.get()
                receiver.read = True
                receiver.save()
            else:
                message = ''
        else:
            message = ''
    except ObjectDoesNotExist:
        message = 'ObjectDoesNotExist'
        print('__ERROR__')
    return render(
        request,
        'mymail/read_message.html', {"message": message, "current_user": current_user}
    )


def redir(request):
    return redirect('received/0')


def search_templates(request, page):
    activate('Europe/Kiev')
    if request.user.is_authenticated:
        current_user = request.user
        messages = Message.objects\
            .filter(sender=current_user, show_template=True).order_by('-id')
        return search(request, page, messages, 'Templates')
    else:
        return render(request, 'mymail/search.html', {'what_search': 'Templates'})


def delete(request, message_url):
    message = get_object_or_404(Message, url=message_url)
    user = request.user
    if user.is_authenticated:
        if message.sender == user:
            message.show = False
            message.save()
        elif user in [r.user for r in message.receivers.all()]:
            r = message.receivers.get(user=user)
            r.show = False
            r.save()
        delete_mess_without_show(message)
    return redirect('search_received', page=0)


def delete_template(request, message_url):
    message = get_object_or_404(Message, url=message_url)
    user = request.user
    if user.is_authenticated and message.sender == user:
        message.show_template = False
        message.save()
        delete_mess_without_show(message)
    return redirect('search_templates', page=0)


def delete_mess_without_show(message):
    if message.show is False and not message.receivers.filter(show=True) and not message.show_template:
        del_shcedule(message)
        message.delete()


def just_delete(request, message_url):
    message = get_object_or_404(Message, url=message_url)
    if request.user == message.sender and message.send_date > now():
        del_shcedule(message)
        message.delete()
    return redirect('home')


def creation(request, form, template=False, message=''):
    if request.method == "POST" and form.is_valid():
        print("request - {}".format(request.POST))
        data = form.cleaned_data
        print('data', data)
        receivers = data.get('receivers')
        title = data.get('title')
        text = data.get('text')
        send_date = data.get('send_date')
        emails = data.get('emails')

        message = Message(sender=request.user, title=title, text=text, send_date=send_date, emails=emails)
        if request.user in receivers:
            message.show_template = True

            if len(receivers) == 1:
                message.show = False
        message.save()
        if emails:
            send_mail_sheduled(message)
        for receiver in receivers.exclude(id=request.user.id):
            r = Receivers(user=receiver, message=message)
            r.save()
        return redirect('send/0')

    return render(request, "mymail/create_message.html", locals())


def create_from_template(request, message_url):
    activate('Europe/Kiev')
    try:
        message = Message.objects.get(url=message_url, sender=request.user)
        initial_dict = {
            "title": message.title,
            "receivers": [r.user for r in message.receivers.all().exclude(user=request.user)],
            "text": message.text,
            "send_date": message.send_date,
            "emails": message.emails
        }
    except ObjectDoesNotExist:
        return redirect('create_message')
    form = MessageForm(request.POST or None, initial=initial_dict)
    return creation(request, form, True, message)


def create_message(request):
    form = MessageForm(request.POST or None)
    return creation(request, form)
