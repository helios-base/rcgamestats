from functools import wraps
from flask import request, jsonify
from flask_login import current_user
from .models import APIKey, UserType


def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Login required."}), 401
            if current_user.type.value not in roles:
                return jsonify({"error": "Unauthorized access."}), 403
            return f(*args, **kwargs)

        return decorated_function
    return decorator


def admin_required(f):
    return roles_required('admin')(f)


def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        """
        Decorator function to check for a valid API key in the request headers.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: JSON response with an error message and a 401 status code if the API key is invalid.
            Otherwise, it returns the decorated function's response.
        """
        api_key = request.headers.get("x-api-key")
        if api_key is None:
            return jsonify({"error": "Missing API key."}), 401
        record = APIKey.query.filter_by(key=api_key).first()
        if record is None:
            return jsonify({"error": "Invalid or missing API key."}), 401
        if record.is_expired():
            return jsonify({"error": "API key has expired."}), 401
        return f(*args, **kwargs)

    return decorated_function


# def admin_api_key_required(f):
#     return admin_required(api_key_required(f))

def admin_api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.args.get('api_key') or request.headers.get('x-api-key')
        if not api_key:
            return jsonify({"error": "API key required."}), 401

        record = APIKey.query.filter_by(key=api_key).first()
        if not record:
            return jsonify({"error": "Invalid API key."}), 401

        if record.user.type != UserType.ADMIN:
            return jsonify({"error": "Admin privileges required."}), 403

        return f(*args, **kwargs)
    return decorated_function
