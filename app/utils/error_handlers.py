from flask import render_template, request, jsonify
from werkzeug.exceptions import HTTPException
import traceback

def register_error_handlers(app):
    """Register error handlers for the application"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(400)
    def bad_request_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Bad request'}), 400
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': error.description}), error.code
        return render_template('errors/generic.html', error=error), error.code
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        # Log the error
        app.logger.error(f'Unhandled exception: {error}')
        app.logger.error(traceback.format_exc())
        
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
