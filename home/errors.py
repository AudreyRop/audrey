import logging
from home import app, db
from flask import render_template, flash, redirect, jsonify, request, url_for


@app.errorhandler(400)
def bad_request_error(error):
    """Handle 400 Bad Request errors."""
    if request.is_json:
        return jsonify({'error': 'Invalid form submission'}), 400
    else:
        flash('Invalid form submission', 'danger')
        return redirect(url_for('chatbot'))


@app.errorhandler(404)
def page_not_found(e):
    logging.error('An error occurred page not found')
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    logging.error('An internal server error occurred.')
    return render_template('500.html'), 500
