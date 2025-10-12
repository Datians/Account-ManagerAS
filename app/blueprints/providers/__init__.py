from flask import Blueprint
providers_bp = Blueprint('providers', __name__, template_folder='templates')
from . import routes  # noqa
