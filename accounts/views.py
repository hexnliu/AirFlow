from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout



def loginPage(request):
    """
    # login page
    # if user name match password on database, login sucessful and go to dash board page
    # if user name doesn't match password, return error message
    """
    if request.user.is_authenticated:
        return redirect('home')    
    else:
        context = {}
        if request.method == 'POST':
            username = request.POST.get('username')
            password =request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.info(request, 'Username OR password is incorrect')
                context["error"]="Username OR password is incorrect"
        return render(request, 'accounts/login.html', context)


def logoutUser(request):
    """ 
    logout method
    go to login page
    """
    logout(request)
    return redirect('login')




