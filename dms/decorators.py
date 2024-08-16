from django.shortcuts import redirect
from django.http import HttpResponseNotFound

def for_admins(function):
    def wrapper(request, *args, **kwargs):
        if request.user.user_type == 'STAFF':
            return redirect('home')
        elif request.user.user_type == 'REVIEWER':
            return redirect('review_folders')
        return function(request, *args, **kwargs)
    return wrapper

def anti_reviewer(function):
    def wrapper(request, *args, **kwargs):
        if request.user.user_type == 'REVIEWER':
            return redirect('review_folders')
        return function(request, *args, **kwargs)
    return wrapper

def for_reviewer(function):
    def wrapper(request, *args, **kwargs):
        if request.user.user_type == 'SUPERADMIN' or request.user.user_type == 'ADMIN':
            return redirect('dashboard')
        elif request.user.user_type == 'STAFF':
            return redirect('home')
        
        return function(request, *args, **kwargs)
    return wrapper

def anti_login(function):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            # if request.user.user_type == 'SUPERADMIN' or request.user.user_type == 'ADMIN':
            #     return redirect('dashboard')
            # elif request.user.user_type == 'STAFF':
            #     return redirect('home')
            # elif request.user.user_type == 'REVIEWER':
            #     return redirect('review_folders')
            return HttpResponseNotFound()
        
        return function(request, *args, **kwargs)
    return wrapper