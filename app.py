"""
Flask Web Application for Aviation Agent

A simple web interface for interacting with the Aviation Agent.
"""

import os
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from aviation_agent import AviationAgent
import secrets

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))

# Store agent instances per session
agents = {}


def get_agent(session_id: str) -> AviationAgent:
    """Get or create an agent for the current session."""
    if session_id not in agents:
        agents[session_id] = AviationAgent()
    return agents[session_id]


@app.route('/')
def index():
    """Render the main page."""
    # Initialize session ID if not present
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages from the user."""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get session ID
        session_id = session.get('session_id')
        if not session_id:
            session['session_id'] = secrets.token_hex(16)
            session_id = session['session_id']
        
        # Get agent for this session
        agent = get_agent(session_id)
        
        # Process message
        response = agent.chat(user_message)
        
        return jsonify({
            'response': response,
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset the conversation for the current session."""
    try:
        session_id = session.get('session_id')
        if session_id and session_id in agents:
            agents[session_id].reset_conversation()
        
        return jsonify({'message': 'Conversation reset successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Aviation Agent'
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
