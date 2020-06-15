
from flask import render_template, request, abort, jsonify
from _request import requester_info as get_requester_info
from utils import json_stringify
from task import new_task, get_task_list_info
from . import main
from .forms import NewSubmitForm


@main.route('/')
def index():
    form = NewSubmitForm()
    return render_template('index.html', form=form)


@main.route('/new', methods=['POST'])
def submit_task():
    form = NewSubmitForm()
    keys = []
    if form.validate():
        urls = [url.strip() for url in form.urls.data.split('\n') if url.strip()]
        keys = []
        for url in urls:
            keys.append(new_task(url))

    return jsonify(keys)


@main.route('/taskListInfo')
def task_list_info():
    return json_stringify(get_task_list_info())


@main.route('/requesterInfo')
def requester_info():
    return json_stringify(get_requester_info())












