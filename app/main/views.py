
from flask import render_template, request, abort

from . import main

@main.route('/new', methods=['POST'])
def submit_task():
    pass




