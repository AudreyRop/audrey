from flask import (
    session, jsonify
)
from flask_login import current_user
from datetime import datetime
from home import db, app


@app.before_request
def before_request():
    if 'user_id' in session:
        session.permanent = True


@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    if current_user.is_authenticated:
        current_user.last_activity = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'User not authenticated'}), 401


@app.route('/leave-site', methods=['POST'])
def leave_site():
    if current_user.is_authenticated:
        current_user.last_activity = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'User not authenticated'}), 401
