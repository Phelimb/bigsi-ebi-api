"""Flask and other extensions instantiated here.
To avoid circular imports with views and create_app(), extensions are instantiated here. They will be initialized
(calling init_app()) in application.py.
"""


from flask_celery import Celery


# from flask.ext.redis import Redis


celery = Celery()
# redis = Redis()
