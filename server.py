import jwt
import requests
import time
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import logging
import os

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Salesforce Configuration ---
SF_INSTANCE_URL = 'https://noscroll-dev-ed.develop.my.salesforce.com'
SF_CLIENT_ID = '3MVG9WVXk15qiz1KZDUVbHP3A5dJFeMHynQ3q2dL59uptrh0WBr.3liHLrecfPVQ4z.60XxnMjQxVog.SpPKt'
SF_USERNAME = 'appdevelopment@sfdc.com'
SF_JWT_KEY_PATH = 'server.key'
SF_LOGIN_URL = 'https://login.salesforce.com'

# Cache for access token
access_token_data = {"token": None, "expires_at": 0}


def get_access_token():
    """
    Generates a JWT and requests an access token from Salesforce.
    The function caches the token to avoid repeated authentication.
    """
    global access_token_data
    if access_token_data["token"] and access_token_data["expires_at"] > time.time() + 60:
        return access_token_data["token"]

   try:
    # First try to read private key from environment variable
    private_key = os.environ.get("SALESFORCE_JWT_KEY")
    if private_key:
        logging.info("✅ Found private key in environment (length: %d)", len(private_key))
    else:
        if not os.path.exists(SF_JWT_KEY_PATH):
            raise FileNotFoundError(f"JWT key file not found at {SF_JWT_KEY_PATH}")
        with open(SF_JWT_KEY_PATH, "r") as key_file:
            private_key = key_file.read()
        logging.info("✅ Loaded private key from file")

    payload = {
        "iss": SF_CLIENT_ID,
        "sub": SF_USERNAME,
        "aud": SF_LOGIN_URL,
        "exp": int(time.time()) + 300  # 5 minutes from now
    }
    encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")

    auth_url = f"{SF_LOGIN_URL}/services/oauth2/token"
    auth_payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": encoded_jwt
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(auth_url, data=auth_payload, headers=headers)
    response.raise_for_status()
    auth_response = response.json()

    if "access_token" in auth_response:
        access_token_data["token"] = auth_response["access_token"]
        access_token_data["expires_at"] = time.time() + auth_response.get("expires_in", 0)
        logging.info("✅ Successfully refreshed Salesforce access token.")
        return access_token_data["token"]
    else:
        raise Exception("Failed to get access token from Salesforce.")

  except Exception as e:
    logging.error(f"Error generating or getting access token: {e}")
    return None


def call_salesforce_api(payload):
    """
    Calls a Salesforce Apex REST endpoint using a generic URL,
    with the specific action passed in the payload.
    """
    access_token = get_access_token()
    if not access_token:
        return {"status": "error", "message": "Failed to authenticate with Salesforce."}

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    # The URL no longer includes a method name, as the Apex class handles routing
    url = f"{SF_INSTANCE_URL}/services/apexrest/NoScroll/v1/"

    try:
        logging.info(f"Calling Salesforce API: {url} with payload: {payload}")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err.response.text}")
        return {"status": "error", "message": f"Salesforce API returned an error: {err.response.text}"}
    except requests.exceptions.RequestException as err:
        logging.error(f"Request error occurred: {err}")
        return {"status": "error", "message": "Network error calling Salesforce API."}


class NoScrollProxy(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self._set_headers(200)

    def do_GET(self):
        """Serve index.html for root, else serve files from /www, else 404."""
        www_root = os.path.join(os.getcwd(), 'www')  # Absolute path to www folder
        # Serve index.html for root
        if self.path == '/':
         file_path = os.path.join(www_root, 'index.html')
        else:
            # Remove leading slash from path and serve from www folder
            file_path = os.path.join(www_root, self.path.lstrip('/'))
         # Check if the file exists
        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.send_response(200)
            # Set content type based on file extension
            if file_path.endswith('.html'):
                content_type = 'text/html'
            elif file_path.endswith('.css'):
                content_type = 'text/css'
            elif file_path.endswith('.js'):
                content_type = 'application/javascript'
            elif file_path.endswith('.json'):
                content_type = 'application/json'
            else:
                content_type = 'application/octet-stream'

            self.send_header('Content-type', content_type)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            with open(file_path, 'rb') as file:
                self.wfile.write(file.read())
        else:
            # File not found
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Not Found"}).encode("utf-8"))            
        
    def do_POST(self):
        """Handle POST requests for API calls."""
        if self.path == "/api/log-usage":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))

                action = request_data.get('action')
                salesforce_response = None

                if action == 'setup':
                    payload = {
                        "action": "setup",
                        "customerName": request_data.get("customerName"),
                        "email": request_data.get("email"),
                        "age": request_data.get("age"),
                        "userType": request_data.get("userType"),
                        "socialMediaApp": request_data.get("socialMediaApp"),
                        "childName": request_data.get("childName"),
                        "childEmail": request_data.get("childEmail")
                    }
                    salesforce_response = call_salesforce_api(payload)

                elif action == 'check_usage':
                    payload = {
                        "action": "check_usage",
                        "customerId": request_data.get("customerId")
                    }
                    salesforce_response = call_salesforce_api(payload)

                elif action == 'log_and_set_time':
                    payload = {
                        "action": "log_and_set_time",
                        "customerId": request_data.get("customerId"),
                        "timeSpent": request_data.get("timeSpent"),
                        "timeLimit": request_data.get("timeLimit")
                    }
                    salesforce_response = call_salesforce_api(payload)
                    
                elif action == 'get_summary':
                    payload = {
                        "action": "get_summary",
                        "customerId": request_data.get("customerId"),
                        "days": request_data.get("days", 3)
                    }
                    salesforce_response = call_salesforce_api(payload)
                    
                elif action == "get_customer_by_email":   # 👈 NEW CASE
                    payload = {
                        "action": "get_customer_by_email",
                        "email": request_data.get("email")
                    }
                    salesforce_response = call_salesforce_api(payload)

                if salesforce_response:
                    self._set_headers(200)
                    response_data = {
                        "status": "success",
                        "message": "Request processed successfully.",
                        "salesforce_response": salesforce_response
                    }
                    self.wfile.write(json.dumps(response_data).encode("utf-8"))
                else:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({
                        "status": "error",
                        "message": f"Bad Request: Invalid or missing action '{action}'"
                    }).encode('utf-8'))

            except json.JSONDecodeError:
                logging.error("JSON Decode Error: Request body is not valid JSON.")
                self._set_headers(400)
                self.wfile.write(json.dumps({"message": "Bad Request: Invalid JSON"}).encode('utf-8'))
            except Exception as e:
                logging.error(f"Error processing POST request: {e}")
                self._set_headers(500)
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": "Internal Server Error",
                    "details": str(e)
                }).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"message": "Not Found"}).encode("utf-8"))


def run(server_class=HTTPServer, handler_class=NoScrollProxy, port=8001):
    """Run the server."""
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    logging.info(f"Starting server on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info("Server stopped.")

if __name__ == '__main__':
    run()
