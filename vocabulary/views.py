from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.conf import settings
from django.core.paginator import Paginator
import os, requests, random
from .models import User
from nltk.tokenize import word_tokenize

#https://api.datamuse.com/words?sp=word&md=f&max=1

def getinfo(rating):
    pwd = os.path.dirname(__file__)
    file = open((pwd + '/static/words.txt'), 'r')
    data = file.readlines()
    choice = random.choice(data)
    try:
        ratinginfo = requests.get(f"https://api.datamuse.com/words?sp={choice}&md=f&max=1").json()[0]
    except:
        print("--------- Bad rating")
        return getinfo(rating)
    wordrating = round(ratinginfo['score']/100) + 650
    print(choice)
    file.close()
    try:
        info = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{choice}").json()[0]
    except:
        print("---------- Bad info")
        return getinfo(rating)
    info['wordrating'] = wordrating
    try:
        print(info['meanings'][0]['definitions'][0]['definition'])
    except:
        return getinfo(rating)
    return info

def index(request):
    if request.user.is_authenticated:
        if request.method == "GET":
            info = getinfo(request.user.rating)
            while True:
                try:
                    while info['phonetics'][0]['audio'] == '':
                        print("--------- Bad audio")
                        return index(request)
                    break
                except:
                    return index(request)
            while True:
                try:
                    example = word_tokenize(info['meanings'][0]['definitions'][0]['example'])
                    word = info['word']
                    if word[-1] == 's':
                        word = word[:-1]
                    j = 0
                    while j != len(example):
                        j = 0
                        f = False
                        for i in example:
                            if i[-1] == 's':
                                i = i[:-1]
                            if i.lower() == word.lower():
                                f = True
                                break
                            print(i.lower())
                            print(word.lower())
                            j += 1
                        if f == True:
                            example[j] = "_____"
                    censored = False
                    for k in example:
                        if k == "_____":
                            censored = True
                            break
                    if censored == False:
                        print("--------- Bad example")
                        return index(request)
                    example = " ".join(example)
                    break
                except:
                    print("---------- Bad example")
                    return index(request)
            return render(request, "quiz.html", {"definition": info['meanings'][0]['definitions'][0]['definition'], "audio": info['phonetics'][0]['audio'], "word": word, "example":example, "wordrating": info['wordrating'], "rating": round(request.user.rating)})
        elif request.method == "POST":
            answer = request.POST['answer']
            guess = request.POST['word']
            info = getinfo(request.user.rating)
            while True:
                try:
                    while info['phonetics'][0]['audio'] == '':
                        print("--------- Bad audio")
                        return index(request)
                    break
                except:
                    return index(request)
            while True:
                try:
                    example = word_tokenize(info['meanings'][0]['definitions'][0]['example'])
                    word = info['word']
                    if word[-1] == 's':
                        word = word[:-1]
                    j = 0
                    while j != len(example):
                        j = 0
                        f = False
                        for i in example:
                            if i[-1] == 's':
                                i = i[:-1]
                            if i.lower() == word.lower():
                                f = True
                                break
                            print(i.lower())
                            print(word.lower())
                            j += 1
                        if f == True:
                            example[j] = "_____"
                    censored = False
                    for k in example:
                        if k == "_____":
                            censored = True
                            break
                    if censored == False:
                        print("--------- Bad example")
                        return index(request)
                    example = " ".join(example)
                    break
                except:
                    print("---------- Bad example")
                    return index(request)
            if answer[-1] == 's':
                answer = answer[:-1]
            if guess[-1] == 's':
                guess = guess[:-1]
            expectedResult = (1/(1 + 10**((info['wordrating'] - request.user.rating)/400)))
            if answer.lower() == guess.lower():
                result = 1
                newrating = request.user.rating + (55 * (result - expectedResult))
                oldrating = request.user.rating
                request.user.rating = newrating
                request.user.save()
                return render(request, "quiz.html", {"definition": info['meanings'][0]['definitions'][0]['definition'], "audio": info['phonetics'][0]['audio'], "word": info['word'], "example":example, "message": "Correct!", "wordrating": info['wordrating'], "rating": f"{round(request.user.rating)} +({abs(round(newrating - oldrating))})"})
            else:
                result = 0
                newrating = request.user.rating + (55 * (result - expectedResult))
                oldrating = request.user.rating
                request.user.rating = newrating
                request.user.save()
                return render(request, "quiz.html", {"definition": info['meanings'][0]['definitions'][0]['definition'], "audio": info['phonetics'][0]['audio'], "word": info['word'], "example":example, "message": f"The correct answer was: {answer}", "wordrating": info['wordrating'], "rating": f"{round(request.user.rating)} ({-abs(round(newrating - oldrating))})"})
    return render(request, "index.html")
def register_view(request):
    if request.method == "POST":
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "index.html", {"error": "Passwords do not match"})
        username = request.POST["username"]
        email = request.POST["email"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        try:
            user = User.objects.create_user(username, email, password, first_name=first_name, last_name=last_name)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "error": "Username already taken."
            })
        if user:
            login(request=request, user=user)
        return HttpResponseRedirect(reverse("index"))
    return render(request, "register.html")

def login_view(request):
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            user = authenticate(email=username, password=password)
            if user:
                login(request=request, user=user)
                return HttpResponseRedirect(reverse("index"))
            return render(request, "login.html", {"error": "Invalid username and/or password"})
    return render(request, "login.html")
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))
