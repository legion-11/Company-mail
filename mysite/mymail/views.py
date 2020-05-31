from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from .forms import UserForm, LoginForm, MessageForm
from .models import Message, Receivers
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils.timezone import activate, now
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail

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


def search(request, page, messages):
    number_print = 30
    more = len(messages) > number_print * (page + 1)
    return render(request, 'mymail/search.html',
                  {"messages": messages[number_print * page: number_print * (page + 1)],
                   "next_page": page + 1,
                   "prev_page": page - 1,
                   "more": more})


def search_received(request, page):
    activate('Europe/Kiev')
    if request.user.is_authenticated:
        current_user = request.user
        messages = Message.objects.filter(receivers__user=current_user) \
            .exclude(send_date__isnull=False, send_date__gt=datetime.datetime.now())\
            .exclude(sender=current_user)\
            .order_by('-id')

        return search(request, page, messages)
    else:
        return render(request, 'mymail/search.html')


def search_send(request, page):
    activate('Europe/Kiev')
    if request.user.is_authenticated:
        current_user = request.user
        messages = Message.objects.filter(sender=current_user).order_by('-id')
        return search(request, page, messages)
    else:
        return render(request, 'mymail/search.html')


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
                    receivers = data.get('receivers')
                    todelete = set([r.user for r in message.receivers.all()]) -set(receivers)
                    to_add = set(receivers) - set([r.user for r in message.receivers.all()])
                    for i in range(min(len(to_add), len(todelete))):
                        message.receivers.get(user=todelete.pop()).user = to_add.pop()
                    for user in to_add:
                        r = Receivers(user=user, message=message)
                        r.save()
                    message.receivers.filter(user__in=todelete).delete()
                    if message.emails:
                        del_shcedule(message)
                    message.emails = data.get('emails')
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
        messages = Message.objects.filter(receivers__user=current_user, sender=current_user).order_by('-id')
        return search(request, page, messages)
    else:
        return render(request, 'mymail/search.html')


def creation(request, form):
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
        if not send_date:
            message.send_date = message.pub_date
        message.save()
        if emails:
            send_mail_sheduled(message)
        if receivers:
            for receiver in receivers:
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
            "receivers": [r.user for r in message.receivers.all()],
            "text": message.text,
            "send_date": message.send_date,
            "emails": message.emails
        }
    except ObjectDoesNotExist:
        return redirect('create_message')
    form = MessageForm(request.POST or None, initial=initial_dict)
    return creation(request, form)


def create_message(request):
    form = MessageForm(request.POST or None)
    return creation(request, form)


def registration(request):
    form = UserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        print("request - {}".format(request.POST))
        data = form.cleaned_data
        print("cleaned data - {}".format(data))

        name = request.POST.get('username')
        password = request.POST.get('password')
        user = User(username=name)

        user.set_password(password)
        user.save()
        user = authenticate(username=name, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')

    return render(request, "mymail/registration.html", locals())


def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST":
        print("request - {}".format(request.POST))
        data = form.cleaned_data
        print("cleaned data - {}".format(data))

        name = request.POST.get('username')
        password = request.POST.get('password')
        user = User(username=name, password=password)
        user = authenticate(username=name, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')

    return render(request, "mymail/login.html", locals())
