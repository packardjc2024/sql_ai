from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings

from .bot_class import ChatBot


###############################################################################
# Views 
###############################################################################
def index(request):
    if 'history' not in request.session:
        request.session['history'] = []
    if 'results' not in request.session:
        request.session['results'] = []
    if 'query' not in request.session:
        request.session['query'] = ''

    if request.session['results']:
        columns = list(request.session['results'][0].keys())
    else:
        columns = []

    context = {
        'history': request.session['history'],
        'results': request.session['results'],
        'columns': columns,
        'query': request.session['query'],
        'count': len(request.session['results']),
    }

    if request.method == 'GET':
        return render(request, 'chatbot/index.html', context)


def query_db(request):
    context = {}
    if request.method == 'POST':
        query = request.POST.get('user-input')
        bot = ChatBot()
        request.session['results'], request.session['query'] = bot.query(query)
        request.session['history'].append({'source': 'user', 'content': query})
    return redirect('chatbot:index')


def clear_history(request):
    request.session.clear()
    return redirect('chatbot:index')
