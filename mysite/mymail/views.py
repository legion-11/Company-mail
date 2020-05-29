from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from .forms import UserForm, LoginForm, MessageForm
from .models import Message
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils.timezone import activate, make_aware
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail

scheduler = BackgroundScheduler()
scheduler.start()


def just_send_mail(message):
    send_mail(message.title, message.text + '\n' + str(message.sender),
              message.sender, message.emails, fail_silently=False)


def send_mail_sheduled(message):
    if message.send_date:
        scheduler.pause()
        scheduler.add_job(func=just_send_mail, trigger='date',
                          run_date=message.send_date, args=[message], id=str(message.url))
        scheduler.resume()
    else:
        just_send_mail(message)


def search_received(request, page):
    if request.user.is_authenticated:
        number_print = 30
        current_user = request.user
        messages = Message.objects.filter(receivers=current_user).exclude(send_date__isnull=False,
                                                                          send_date__gt=datetime.datetime.now())
        more = len(messages) > number_print * (page + 1)
        return render(request, 'mymail/search.html',
                      {"messages": messages[number_print * page: number_print * (page + 1)],
                       "next_page": page + 1,
                       "prev_page": page - 1,
                       "more": more})
    else:
        return render(request, 'mymail/search.html')


def search_send(request, page):
    if request.user.is_authenticated:
        number_print = 30
        current_user = request.user
        messages = Message.objects.filter(sender=current_user)
        more = len(messages) > number_print * (page + 1)
        return render(request, 'mymail/search.html',
                      {"messages": messages[number_print * page: number_print * (page + 1)],
                       "next_page": page + 1,
                       "prev_page": page - 1,
                       "more": more})
    else:
        return render(request, 'mymail/search.html')


def read_message(request, message_url):
    current_user = request.user
    try:
        message = Message.objects.get(url=str(message_url))
        if not (current_user in message.receivers.all() or current_user is message.sender):
            message = ''
    except ObjectDoesNotExist:
        message = ''
    return render(
        request,
        'mymail/read_message.html', {"message": message}
    )


def redir(request):
    return redirect('received/0')


def create_message(request):
    activate('Europe/Kiev')
    form = MessageForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        print("request - {}".format(request.POST))
        data = form.cleaned_data
        print('data', data)
        receivers = data.get('receivers')
        title = data.get('title')
        text = data.get('text')
        send_date = data.get('send_date')
        emails = data.get('emails')
        message = Message(sender=request.user, title=title, text=text, send_date=make_aware(send_date), emails=emails)
        message.save()

        if emails:
            send_mail_sheduled(message)
        if receivers:
            for receiver in receivers:
                message.receivers.add(receiver)
            message.save()
    return render(request, "mymail/create_message.html", locals())


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
