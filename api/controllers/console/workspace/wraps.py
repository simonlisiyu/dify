# [Starry] directory
# __author__ "lisiyu"
# date 2024/8/26
from functools import wraps

from flask_login import current_user
from flask_restful import Resource
from werkzeug.exceptions import NotFound

from controllers.console.wraps import account_initialization_required
from extensions.ext_database import db
from libs.login import login_required
from models.model import Directory


def directory_required(view=None):
    def decorator(view):
        @wraps(view)
        def decorated(*args, **kwargs):
            if not kwargs.get('directory_id'):
                raise ValueError('missing directory_id in path parameters')

            directory_id = kwargs.get('directory_id')
            directory_id = str(directory_id)

            del kwargs['directory_id']

            directory = db.session.query(Directory).filter(
                Directory.id == directory_id,
                Directory.tenant_id == current_user.current_tenant_id
            ).first()

            if directory is None:
                raise NotFound(f'Directory {directory_id} not found')

            return view(directory, *args, **kwargs)
        return decorated

    if view:
        return decorator(view)
    return decorator


class DirectoryResource(Resource):
    # must be reversed if there are multiple decorators
    method_decorators = [directory_required, account_initialization_required, login_required]
