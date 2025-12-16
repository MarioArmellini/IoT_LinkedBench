#!/usr/bin/env python3
"""
REST API for LinkedBench system
Provides endpoints for status, control, and data access
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

try:
    from flask import Flask, jsonify, request
    from flask_cors import CORS
except ImportError:
    Flask = None
    CORS = None

if TYPE_CHECKING:
    from linkedbench import LinkedBenchSystem

logger = logging.getLogger('LinkedBench.API')


def create_app(system: 'LinkedBenchSystem') -> Flask:
    """Create Flask application"""
    
    if Flask is None:
        logger.error("Flask not installed, REST API disabled")
        return None
    
    app = Flask(__name__)
    
    # Enable CORS for cross-origin requests
    if CORS:
        CORS(app)
    
    # Store system reference
    app.config['LINKEDBENCH_SYSTEM'] = system
    
    @app.route('/')
    def index():
        """API root"""
        return jsonify({
            'name': 'LinkedBench API',
            'version': '1.0.0',
            'bench_id': system.bench_id,
            'endpoints': {
                'status': '/api/status',
                'events': '/api/events',
                'statistics': '/api/statistics',
                'mode': '/api/mode'
            }
        })
    
    @app.route('/api/status')
    def get_status():
        """Get current bench status"""
        try:
            status = system.get_status()
            return jsonify(status), 200
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/mode', methods=['GET', 'POST'])
    def mode():
        """Get or set mode"""
        if request.method == 'GET':
            try:
                status = system.get_status()
                return jsonify({
                    'mode': status['mode'],
                    'mode_name': status['mode_name']
                }), 200
            except Exception as e:
                logger.error(f"Error getting mode: {e}")
                return jsonify({'error': str(e)}), 500
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                
                if not data or 'mode' not in data:
                    return jsonify({'error': 'mode field required'}), 400
                
                mode = data['mode']
                
                if not isinstance(mode, int) or mode < 0 or mode > 3:
                    return jsonify({'error': 'Invalid mode value (0-3)'}), 400
                
                status = system.set_mode(mode)
                return jsonify(status), 200
                
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                logger.error(f"Error setting mode: {e}")
                return jsonify({'error': str(e)}), 500
    
    @app.route('/api/events')
    def get_events():
        """Get event history"""
        try:
            # Query parameters
            limit = request.args.get('limit', default=100, type=int)
            offset = request.args.get('offset', default=0, type=int)
            event_type = request.args.get('type', default=None, type=str)
            
            # Validate limits
            limit = min(max(1, limit), 1000)
            offset = max(0, offset)
            
            events = system.db.get_events(
                bench_id=system.bench_id,
                limit=limit,
                offset=offset,
                event_type=event_type
            )
            
            return jsonify({
                'events': events,
                'count': len(events),
                'limit': limit,
                'offset': offset
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/events/<int:event_id>')
    def get_event(event_id):
        """Get specific event by ID"""
        try:
            event = system.db.get_event_by_id(event_id)
            
            if event:
                return jsonify(event), 200
            else:
                return jsonify({'error': 'Event not found'}), 404
                
        except Exception as e:
            logger.error(f"Error getting event: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/statistics')
    def get_statistics():
        """Get usage statistics"""
        try:
            days = request.args.get('days', default=7, type=int)
            days = min(max(1, days), 365)
            
            stats = system.db.get_statistics(
                bench_id=system.bench_id,
                days=days
            )
            
            return jsonify(stats), 200
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'bench_id': system.bench_id
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


def start_api_server(system: 'LinkedBenchSystem', host: str = '0.0.0.0', port: int = 5000):
    """Start the Flask API server"""
    
    if Flask is None:
        logger.warning("Flask not available, REST API not started")
        return
    
    try:
        app = create_app(system)
        
        if app:
            logger.info(f"Starting REST API server on {host}:{port}")
            app.run(host=host, port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to start API server: {e}", exc_info=True)
