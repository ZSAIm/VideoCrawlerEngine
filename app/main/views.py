
from flask import render_template, jsonify
from uitls import json_stringify
from flow import TaskStack
from . import main
from .forms import NewSubmitForm


@main.route('/')
def index():
    form = NewSubmitForm()
    return render_template('index.html', form=form)


@main.route('/new', methods=['POST'])
def submit_task():
    form = NewSubmitForm()
    task_resp = []
    if form.validate():
        urls = [url.strip() for url in form.urls.data.split('\n') if url.strip()]
        task_resp = [TaskStack.new(url,) for url in urls]
    return jsonify(task_resp)


@main.route('/lstTasks')
def lst_tasks():
    return json_stringify(TaskStack.simple_all())




