"""Pytest fixtures — SQLite in-memory via TestConfig."""
import pytest

from app import create_app
from config import TestConfig
from models import db


@pytest.fixture
def app():
    flask_app, _socketio = create_app(TestConfig)
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def db_session(app):
    return db.session
