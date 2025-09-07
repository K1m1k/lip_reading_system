from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from database import DatabaseManager
from typing import Dict, Any

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class DashboardAPI:
    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        self.db = db_manager
        self.config = config
        self.setup_routes()
    
    def setup_routes(self):
        @app.route('/api/detections', methods=['GET'])
        def get_detections():
            try:
                limit = request.args.get('limit', 100)
                offset = request.args.get('offset', 0)
                
                with self.db.connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM detections 
                        ORDER BY timestamp DESC 
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    
                    detections = cursor.fetchall()
                    return jsonify({
                        'success': True,
                        'data': detections,
                        'count': len(detections)
                    })
            except Exception as e:
                logger.error(f"Errore API detections: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @app.route('/api/blacklist', methods=['GET', 'POST', 'DELETE'])
        def manage_blacklist():
            try:
                if request.method == 'GET':
                    with self.db.connection.cursor() as cursor:
                        cursor.execute("SELECT phrase FROM blacklist ORDER BY phrase")
                        phrases = [row[0] for row in cursor.fetchall()]
                        return jsonify({'success': True, 'data': phrases})
                
                elif request.method == 'POST':
                    data = request.get_json()
                    phrase = data.get('phrase')
                    
                    if not phrase:
                        return jsonify({'success': False, 'error': 'Phrase required'}), 400
                    
                    success = self.db.add_to_blacklist(phrase, 'dashboard')
                    return jsonify({'success': success})
                
                elif request.method == 'DELETE':
                    phrase = request.args.get('phrase')
                    
                    if not phrase:
                        return jsonify({'success': False, 'error': 'Phrase required'}), 400
                    
                    with self.db.connection.cursor() as cursor:
                        cursor.execute("DELETE FROM blacklist WHERE phrase = %s", (phrase,))
                        self.db.connection.commit()
                        return jsonify({'success': True})
            
            except Exception as e:
                logger.error(f"Errore API blacklist: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @app.route('/api/stats', methods=['GET'])
        def get_stats():
            try:
                timeframe = request.args.get('timeframe', 'today')
                
                with self.db.connection.cursor() as cursor:
                    if timeframe == 'today':
                        cursor.execute("""
                            SELECT COUNT(*) as count, 
                                   DATE(timestamp) as date 
                            FROM detections 
                            WHERE DATE(timestamp) = CURRENT_DATE 
                            GROUP BY DATE(timestamp)
                        """)
                    else:
                        cursor.execute("""
                            SELECT COUNT(*) as count, 
                                   DATE(timestamp) as date 
                            FROM detections 
                            WHERE timestamp >= NOW() - INTERVAL '7 days' 
                            GROUP BY DATE(timestamp) 
                            ORDER BY date
                        """)
                    
                    detection_stats = cursor.fetchall()
                    
                    cursor.execute("""
                        SELECT phrase, COUNT(*) as count 
                        FROM detections 
                        GROUP BY phrase 
                        ORDER BY count DESC 
                        LIMIT 10
                    """)
                    
                    top_phrases = cursor.fetchall()
                    
                    return jsonify({
                        'success': True,
                        'detection_stats': detection_stats,
                        'top_phrases': top_phrases
                    })
            
            except Exception as e:
                logger.error(f"Errore API stats: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
