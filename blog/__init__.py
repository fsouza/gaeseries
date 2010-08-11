from flask import Flask
import settings

app = Flask('blog')
app.config.from_module('blog.settings')

import views
