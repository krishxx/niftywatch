from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import sys
import json
import pickle
from datetime import datetime
from breeze_connect import BreezeConnect

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables for session management
isec_session = None
session_created_at = None
SESSION_TIMEOUT = 3600  # 1 hour timeout

# Account configuration (moved from get_idx.py)
session_key_inv = 0
session_key_raju = 52120565
session_key_swaran = 0
session_key_moses = 0
session_key_hada = 0

moses_account = '{"appKey" : "396C!u2213c1a3z2x743467h*G8^y&+7","apiSecret" : "77911&198C6!86bt72Io8tid27222789"}'
raju_account = '{"appKey" : "i87W5a354o436C172$1954914Uj1s54m","apiSecret" : "5B2M47139O29953437a)O37`91h6f3l2"}'
swaran_account = '{"appKey" : "F005#727V890J99965G632z9h9285q23","apiSecret" : "z26A3(w9C635&2F89402L24k420b6209"}'
hada_account = '{"appKey" : "054222`234~4mzP58=E1&X885V8C1624","apiSecret" : "9193^72G6R2a8~3897jbR2X9UH3C8568"}'

# login_dtls_dict = {"appKey" : config_icici.appKey,"apiSecret" :config_icici.apiSecret}
# inv_account = json.dumps(login_dtls_dict)

# use_account = json.loads(moses_account)
# session_key = session_key_moses

use_account = json.loads(raju_account)
session_key = session_key_raju

# use_account = json.loads(swaran_account)
# session_key = session_key_swaran

# use_account = json.loads(hada_account)
# session_key = session_key_hada

# use_account = json.loads(inv_account)
# session_key = session_key_inv


def breeze_login():
    """Login to Breeze API and return session object"""
    global isec_session, session_created_at
    
    try:
        print(f'Logging in with appKey=[{use_account["appKey"]}] :: session_key=[{session_key}]')
        
        # Initialize SDK
        isec = BreezeConnect(api_key=use_account['appKey'])    
        isec.generate_session(api_secret=use_account['apiSecret'], session_token=session_key)
        
        # Store session globally
        isec_session = isec
        session_created_at = datetime.now()
        
        print(f"Login successful at {session_created_at}")
        return isec
        
    except Exception as e:
        print(f"Login failed: {str(e)}")
        return None

def get_or_create_session():
    """Get existing session or create new one if needed"""
    global isec_session, session_created_at
    
    # Check if we have a valid session
    if isec_session is None or session_created_at is None:
        print("No existing session, creating new one...")
        return breeze_login()
    
    # Check if session is expired
    session_age = (datetime.now() - session_created_at).total_seconds()
    if session_age > SESSION_TIMEOUT:
        print(f"Session expired ({session_age:.0f}s old), creating new one...")
        return breeze_login()
    
    print(f"Using existing session ({session_age:.0f}s old)")
    return isec_session

def save_session_to_file():
    """Save session object to file for get_idx.py to use"""
    if isec_session:
        try:
            with open('session.pkl', 'wb') as f:
                pickle.dump(isec_session, f)
            print("Session saved to session.pkl")
            return True
        except Exception as e:
            print(f"Failed to save session: {str(e)}")
            return False
    return False

@app.route('/refresh-data', methods=['POST'])
def refresh_data():
    try:
        data = request.get_json()
        selected_date = data.get('date', '')
        selected_index = data.get('index', 'NIFTY')
        
        if not selected_date:
            return jsonify({'error': 'Date is required'}), 400
        
        # Get or create session
        session = get_or_create_session()
        if not session:
            return jsonify({'error': 'Failed to create trading session'}), 500
        
        # Save session to file for get_idx.py to use
        if not save_session_to_file():
            return jsonify({'error': 'Failed to save session for script'}), 500
        
        # Map UI index names to script symbols
        symbol_mapping = {
            'NIFTY': 'NIFTY',
            'BANK NIFTY': 'CNXBAN'
        }
        
        script_symbol = symbol_mapping.get(selected_index, selected_index)
          # Validate date format
        try:
            datetime.strptime(selected_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        print(f"Executing get_idx.py with date: {selected_date}, index: {selected_index} (script symbol: {script_symbol})")
        print(f"Using existing session, no need to login again")
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        get_idx_path = os.path.join(current_dir, 'get_idx.py')
          # Execute the Python script with the selected date and symbol (no login needed)
        process = subprocess.run([
            sys.executable, get_idx_path, selected_date, script_symbol, '--use-saved-session'
        ], capture_output=True, text=True, cwd=current_dir)
        
        if process.returncode == 0:
            print(f"Script executed successfully for {selected_index} ({script_symbol}) on {selected_date}")
            return jsonify({
                'success': True, 
                'message': f'Data refreshed successfully for {selected_index} on {selected_date}',
                'output': process.stdout
            })
        else:
            print(f"Script execution failed: {process.stderr}")
            return jsonify({
                'success': False, 
                'error': f'Script execution failed: {process.stderr}',
                'output': process.stdout
            }), 500
            
    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'Server is running'})

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Server will be available at http://localhost:5000")
    
    # Initialize session on startup
    print("Initializing trading session...")
    session = get_or_create_session()
    if session:
        print("Initial session created successfully")
        save_session_to_file()
    else:
        print("Warning: Failed to create initial session")
    
    app.run(debug=True, host='localhost', port=5000)
