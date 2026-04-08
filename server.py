"""
OpenEnv API Server

Minimal HTTP server that exposes the CustomerSupportEnv as a web service.
This is required for OpenEnv validation to work - the validator pings /reset endpoint.
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from customer_support_env import CustomerSupportEnv, TaskType, Action

# Global environment instance (shared across all requests)
_env = None
_task_type = None

# Configuration
SEED = int(os.getenv("CUSTOMER_SUPPORT_SEED", "42"))
TASK_NAME = os.getenv("CUSTOMER_SUPPORT_TASK", "email_triage")
PORT = int(os.getenv("PORT", "8000"))

# Task type mapping
TASK_MAP = {
    "email_triage": TaskType.EASY,
    "ticket_priority": TaskType.MEDIUM,
    "multi_turn_resolution": TaskType.HARD,
}


class OpenEnvHandler(BaseHTTPRequestHandler):
    """HTTP handler for OpenEnv API endpoints."""
    
    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        pass
    
    def do_POST(self):
        """Handle POST requests to /reset, /step, /state."""
        path = urlparse(self.path).path
        global _env, _task_type
        
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
            
            try:
                request_data = json.loads(body) if body else {}
            except:
                request_data = {}
            
            if path == '/reset':
                # Initialize environment if needed
                if _env is None:
                    _task_type = TASK_MAP.get(TASK_NAME, TaskType.EASY)
                    _env = CustomerSupportEnv(task_type=_task_type, seed=SEED)
                
                # Reset environment
                obs = _env.reset()
                
                response = {
                    "observation": {
                        "ticket_id": obs.ticket_id,
                        "customer_message": obs.customer_message,
                        "previous_context": obs.previous_context,
                        "customer_sentiment": obs.customer_sentiment,
                    },
                    "info": {}
                }
                self._send_json(200, response)
            
            elif path == '/step':
                if _env is None:
                    self._send_json(400, {"error": "Environment not initialized. Call /reset first."})
                    return
                
                # Parse action from request body
                action_dict = request_data.get('action', {})
                
                try:
                    action = Action(
                        task_type=_env.task_type,
                        action_type=action_dict.get('action_type', 'respond'),
                        category=action_dict.get('category'),
                        priority=action_dict.get('priority'),
                        suggested_next_step=action_dict.get('suggested_next_step'),
                        response_text=action_dict.get('response_text'),
                    )
                except Exception as e:
                    self._send_json(400, {"error": f"Invalid action: {str(e)}"})
                    return
                
                # Execute step
                obs, reward, done, info = _env.step(action)
                
                response = {
                    "observation": {
                        "ticket_id": obs.ticket_id,
                        "customer_message": obs.customer_message,
                        "previous_context": obs.previous_context,
                        "customer_sentiment": obs.customer_sentiment,
                    },
                    "reward": reward.total_reward,
                    "done": done,
                    "info": info or {}
                }
                self._send_json(200, response)
            
            elif path == '/state':
                if _env is None:
                    self._send_json(400, {"error": "Environment not initialized. Call /reset first."})
                    return
                
                state = _env.state()
                response = {"state": state}
                self._send_json(200, response)
            
            else:
                self._send_json(404, {"error": "Not found"})
        
        except Exception as e:
            self._send_json(500, {"error": str(e)})
    
    def do_GET(self):
        """Handle GET requests for health check."""
        path = urlparse(self.path).path
        
        if path == '/health' or path == '/':
            response = {
                "status": "ok",
                "task": TASK_NAME,
                "environment": "AI Customer Support Resolution System"
            }
            self._send_json(200, response)
        else:
            self._send_json(404, {"error": "Not found"})
    
    def _send_json(self, status_code, data):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def main():
    """Start the API server."""
    print(f"Starting OpenEnv API server on port {PORT}", file=sys.stderr)
    print(f"Task: {TASK_NAME}, Seed: {SEED}", file=sys.stderr)
    
    server = HTTPServer(('0.0.0.0', PORT), OpenEnvHandler)
    
    print(f"Server ready at http://0.0.0.0:{PORT}", file=sys.stderr)
    print("Endpoints:", file=sys.stderr)
    print("  POST /reset   - Reset environment", file=sys.stderr)
    print("  POST /step    - Execute one step", file=sys.stderr)
    print("  POST /state   - Get state", file=sys.stderr)
    print("  GET  /health  - Health check", file=sys.stderr)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server shutting down...", file=sys.stderr)
        server.shutdown()


if __name__ == "__main__":
    main()
