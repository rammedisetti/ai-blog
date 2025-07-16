from django.shortcuts import render

def home(request):
    from datetime import datetime
    context = {'year': datetime.now().year}
    return render(request, 'blog/landing.html', context)