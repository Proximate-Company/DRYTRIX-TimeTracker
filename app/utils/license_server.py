import os
import json
import uuid
import time
import threading
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import platform
import socket

logger = logging.getLogger(__name__)

class LicenseServerClient:
    """Client for communicating with the Metrics Server"""
    
    def __init__(self, app_identifier: str = "timetracker", app_version: str = "1.0.0"):
        # Server configuration (env-overridable)
        # Default targets the public metrics endpoint; override via environment if needed.
        default_server_url = "http://metrics.drytrix.com:58082"
        configured_server_url = os.getenv("METRICS_SERVER_URL", os.getenv("LICENSE_SERVER_BASE_URL", default_server_url))
        self.server_url = self._normalize_base_url(configured_server_url)
        self.api_key = os.getenv("METRICS_SERVER_API_KEY", os.getenv("LICENSE_SERVER_API_KEY", "no-license-required"))
        self.app_identifier = app_identifier
        self.app_version = app_version
        
        # Instance management
        self.instance_id = None
        self.registration_token = None
        self.is_registered = False
        self.heartbeat_thread = None
        # Timing configuration
        self.heartbeat_interval = int(os.getenv("METRICS_HEARTBEAT_SECONDS", os.getenv("LICENSE_HEARTBEAT_SECONDS", "3600")))  # default: 1 hour
        self.request_timeout = int(os.getenv("METRICS_SERVER_TIMEOUT_SECONDS", os.getenv("LICENSE_SERVER_TIMEOUT_SECONDS", "30")))  # default: 30s per docs
        self.running = False
        
        # System information
        self.system_info = self._collect_system_info()

        logger.info(f"Metrics server configured: base='{self.server_url}', app='{self.app_identifier}', version='{self.app_version}'")
        if not self.api_key:
            logger.warning("X-API-Key is empty; server may reject requests. Set LICENSE_SERVER_API_KEY.")

        # Registration synchronization and persistence
        self._registration_lock = threading.Lock()
        self._registration_in_progress = False
        self._state_file_path = self._compute_state_file_path()
        self._load_persisted_state()
        
        # Offline storage for failed requests
        self.offline_data = []
        self.max_offline_data = 100
        
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information for registration"""
        try:
            # Check if analytics are allowed
            from app.models import Settings
            try:
                settings = Settings.get_settings()
                if not settings.allow_analytics:
                    # Return minimal info if analytics are disabled
                    return {
                        "os": "Unknown",
                        "version": "Unknown",
                        "architecture": "Unknown",
                        "machine": "Unknown",
                        "processor": "Unknown",
                        "hostname": "Unknown",
                        "local_ip": "Unknown",
                        "python_version": "Unknown",
                        "analytics_disabled": True
                    }
            except Exception:
                # If we can't get settings, assume analytics are allowed (fallback)
                pass
            
            # Get local IP address
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            return {
                "os": platform.system(),
                "version": platform.version(),
                "architecture": platform.architecture()[0],
                "machine": platform.machine(),
                "processor": platform.processor(),
                "hostname": hostname,
                "local_ip": local_ip,
                "python_version": platform.python_version(),
                "analytics_disabled": False
            }
        except Exception as e:
            logger.warning(f"Could not collect complete system info: {e}")
            return {
                "os": platform.system(),
                "version": "unknown",
                "architecture": "unknown",
                "analytics_disabled": False
            }

    def _normalize_base_url(self, base_url: str) -> str:
        """Normalize base URL to avoid duplicate '/api/v1' when building endpoints.

        Accepts values with or without trailing slash and with or without '/api/v1'.
        Always returns a URL WITHOUT trailing slash and WITHOUT '/api/v1'.
        """
        try:
            if not base_url:
                return ""
            url = base_url.strip().rstrip("/")
            # If caller provided a base that already includes '/api/v1', strip it.
            if url.endswith("/api/v1"):
                url = url[: -len("/api/v1")]
                url = url.rstrip("/")
            return url
        except Exception:
            # Fallback to provided value if normalization fails
            return base_url

    def _compute_state_file_path(self) -> str:
        """Compute a per-user path to persist license client state (instance id, token)."""
        try:
            if os.name == "nt":
                base_dir = os.getenv("APPDATA") or os.path.expanduser("~")
                app_dir = os.path.join(base_dir, "TimeTracker")
            else:
                app_dir = os.path.join(os.path.expanduser("~"), ".timetracker")
            os.makedirs(app_dir, exist_ok=True)
            return os.path.join(app_dir, "license_client_state.json")
        except Exception:
            # Fallback to current directory
            return os.path.join(os.getcwd(), "license_client_state.json")

    def _load_persisted_state(self):
        """Load previously persisted state if available (instance id, token)."""
        try:
            if self._state_file_path and os.path.exists(self._state_file_path):
                with open(self._state_file_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                loaded_instance_id = state.get("instance_id")
                loaded_token = state.get("registration_token")
                if loaded_instance_id and not self.instance_id:
                    self.instance_id = loaded_instance_id
                if loaded_token:
                    self.registration_token = loaded_token
                logger.info(f"Loaded persisted license client state from '{self._state_file_path}'")
        except Exception as e:
            logger.warning(f"Failed to load persisted license client state: {e}")

    def _persist_state(self):
        """Persist current state (instance id, token) to disk."""
        try:
            if not self._state_file_path:
                return
            state = {
                "instance_id": self.instance_id,
                "registration_token": self.registration_token,
                "app_identifier": self.app_identifier,
                "app_version": self.app_version,
                "updated_at": datetime.now().isoformat()
            }
            with open(self._state_file_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            logger.debug(f"Persisted license client state to '{self._state_file_path}'")
        except Exception as e:
            logger.warning(f"Failed to persist license client state: {e}")
    
    def get_detailed_error_info(self, response) -> Dict[str, Any]:
        """Extract detailed error information from a failed response"""
        error_info = {
            "status_code": response.status_code,
            "reason": response.reason,
            "headers": dict(response.headers),
            "text": response.text,
            "url": response.url,
            "elapsed": str(response.elapsed) if hasattr(response, 'elapsed') else "unknown"
        }
        
        # Try to parse JSON error response
        try:
            error_json = response.json()
            error_info["json_error"] = error_json
            if "error" in error_json:
                error_info["error_message"] = error_json["error"]
            if "details" in error_json:
                error_info["error_details"] = error_json["details"]
            if "traceback" in error_json:
                error_info["server_traceback"] = error_json["traceback"]
        except json.JSONDecodeError:
            error_info["json_error"] = None
            error_info["parse_error"] = "Response is not valid JSON"
        
        return error_info

    def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Dict]:
        """Make HTTP request to phone home endpoint with error handling"""
        url = f"{self.server_url}{endpoint}"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Log request details
        logger.info(f"Making {method} request to phone home endpoint: {url}")
        if data:
            logger.debug(f"Request data: {json.dumps(data, indent=2)}")
        logger.debug(f"Request headers: {headers}")
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=self.request_timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=self.request_timeout)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            # Log response details
            logger.info(f"Phone home response: {response.status_code} - {response.reason}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            if response.status_code in [200, 201]:
                try:
                    response_json = response.json()
                    logger.debug(f"Response body: {json.dumps(response_json, indent=2)}")
                    return response_json
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Raw response text: {response.text}")
                    return None
            else:
                # Enhanced error logging with detailed error info
                error_info = self.get_detailed_error_info(response)
                logger.error(f"Phone home request failed with status {response.status_code}")
                logger.error(f"Detailed error info: {json.dumps(error_info, indent=2)}")
                
                # Log specific error details
                if "error_message" in error_info:
                    logger.error(f"Server error message: {error_info['error_message']}")
                if "error_details" in error_info:
                    logger.error(f"Server error details: {error_info['error_details']}")
                if "server_traceback" in error_info:
                    logger.error(f"Server traceback: {error_info['server_traceback']}")
                
                return None
                
        except requests.exceptions.Timeout as e:
            logger.error(f"Phone home request timed out after {self.request_timeout} seconds: {e}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Phone home connection error: {e}")
            logger.error(f"URL attempted: {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Phone home request exception: {e}")
            logger.error(f"Request type: {type(e).__name__}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in phone home request: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def register_instance(self) -> bool:
        """Register this instance with the phone home service"""
        with self._registration_lock:
            if self.is_registered:
                logger.info("Instance already registered")
                return True

            # Generate instance ID if not exists (prefer persisted one)
            if not self.instance_id:
                self.instance_id = str(uuid.uuid4())

            registration_data = {
                "app_identifier": self.app_identifier,
                "version": self.app_version,
                "instance_id": self.instance_id,
                "system_metadata": self.system_info,
                "country": "Unknown",  # Could be enhanced with IP geolocation
                "city": "Unknown",
                "license_id": "NO-LICENSE-REQUIRED"
            }

            logger.info(f"Registering instance {self.instance_id} with phone home service at {self.server_url}")
            logger.info(f"App identifier: {self.app_identifier}, Version: {self.app_version}")
            logger.debug(f"System info: {json.dumps(self.system_info, indent=2)}")
            logger.debug(f"Full registration data: {json.dumps(registration_data, indent=2)}")

            response = self._make_request("/api/v1/register", "POST", registration_data)

            if response and "instance_id" in response:
                self.instance_id = response["instance_id"]
                self.registration_token = response.get("token")
                self.is_registered = True
                self._persist_state()
                logger.info(f"Successfully registered instance {self.instance_id}")
                if self.registration_token:
                    logger.debug(f"Received registration token: {self.registration_token[:10]}...")
                return True
            else:
                logger.error(f"Registration failed - no valid response from phone home service")
                logger.error(f"Expected 'instance_id' in response, but got: {response}")
                logger.info(f"Phone home service at {self.server_url} is not available - continuing without registration")
                return False
    
    def validate_license(self) -> bool:
        """Validate license (always returns True since no license required)"""
        if not self.is_registered:
            logger.warning("Cannot validate license: instance not registered")
            return False
            
        validation_data = {
            "app_identifier": self.app_identifier,
            "license_id": "NO-LICENSE-REQUIRED",
            "instance_id": self.instance_id
        }
        
        # Log the complete license validation request (URL, method, headers, body)
        validation_url = f"{self.server_url}/api/v1/validate"
        validation_headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            logger.info("Complete license validation request:")
            logger.info(json.dumps({
                "url": validation_url,
                "method": "POST",
                "headers": validation_headers,
                "body": validation_data
            }, indent=2))
        except Exception:
            # Fallback logging if JSON serialization fails for any reason
            logger.info(f"License validation URL: {validation_url}")
            logger.info(f"License validation headers: {validation_headers}")
            logger.info(f"License validation body: {validation_data}")

        logger.info("Validating metrics token (no license required)")
        response = self._make_request("/api/v1/validate", "POST", validation_data)
        
        if response and response.get("valid", False):
            logger.info("Phone home token validation successful")
            return True
        else:
            logger.warning("Phone home token validation failed")
            return False
    
    def send_heartbeat(self) -> bool:
        """Send heartbeat to phone home service"""
        if not self.is_registered:
            logger.warning("Cannot send heartbeat: instance not registered")
            return False
            
        heartbeat_data = {
            "instance_id": self.instance_id
        }
        
        logger.debug("Sending heartbeat to phone home service")
        response = self._make_request("/api/v1/heartbeat", "POST", heartbeat_data)
        
        if response:
            logger.debug("Heartbeat successful")
            return True
        else:
            logger.warning("Heartbeat failed")
            return False
    
    def send_usage_data(self, data_points: List[Dict[str, Any]]) -> bool:
        """Send usage data to phone home service"""
        if not self.is_registered:
            # Store data offline for later transmission
            self._store_offline_data(data_points)
            return False
        
        # Check if analytics are allowed
        try:
            from app.models import Settings
            settings = Settings.get_settings()
            if not settings.allow_analytics:
                logger.info("Analytics disabled by user setting - skipping usage data transmission")
                return True  # Return True to indicate "success" (data was handled appropriately)
        except Exception:
            # If we can't get settings, assume analytics are allowed (fallback)
            pass
            
        usage_data = {
            "app_identifier": self.app_identifier,
            "instance_id": self.instance_id,
            "data": data_points
        }
        
        logger.debug(f"Sending {len(data_points)} usage data points")
        response = self._make_request("/api/v1/data", "POST", usage_data)
        
        if response:
            logger.debug("Usage data sent successfully")
            # Try to send any stored offline data
            self._send_offline_data()
            return True
        else:
            logger.warning("Failed to send usage data")
            self._store_offline_data(data_points)
            return False
    
    def _store_offline_data(self, data_points: List[Dict[str, Any]]):
        """Store data points for offline transmission"""
        for point in data_points:
            # Use local time per project preference
            point["timestamp"] = datetime.now().isoformat()
            self.offline_data.append(point)
            
        # Keep only the most recent data points
        if len(self.offline_data) > self.max_offline_data:
            self.offline_data = self.offline_data[-self.max_offline_data:]
            
        logger.debug(f"Stored {len(data_points)} data points offline")
    
    def _send_offline_data(self):
        """Attempt to send stored offline data"""
        if not self.offline_data:
            return
            
        data_to_send = self.offline_data.copy()
        self.offline_data.clear()
        
        logger.info(f"Attempting to send {len(data_to_send)} offline data points to phone home service")
        if self.send_usage_data(data_to_send):
            logger.info("Successfully sent offline data")
        else:
            # Put the data back if sending failed
            self.offline_data.extend(data_to_send)
            logger.warning("Failed to send offline data, will retry later")
    
    def _heartbeat_worker(self):
        """Background worker for sending heartbeats"""
        while self.running:
            try:
                if self.is_registered:
                    self.send_heartbeat()
                else:
                    # If not registered, try to register again every hour
                    logger.debug("Attempting to register with phone home service...")
                    self.register_instance()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Error in heartbeat worker: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def start(self) -> bool:
        """Start the phone home client"""
        if self.running:
            logger.warning("Phone home client already running")
            return True
            
        logger.info(f"Starting phone home client (instance: {id(self)})")
        
        # Try to register instance (but don't fail if it doesn't work)
        registration_success = self.register_instance()
        if not registration_success:
            logger.info("Phone home service not available - client will run in offline mode")
        
        # Start heartbeat thread
        self.running = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_worker, daemon=True)
        self.heartbeat_thread.start()
        
        logger.info(f"Phone home client started successfully (instance: {id(self)})")
        return True
    
    def stop(self):
        """Stop the phone home client"""
        logger.info("Stopping phone home client")
        self.running = False
        
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=5)
        
        logger.info("Phone home client stopped")
    
    def check_server_health(self) -> bool:
        """Check if the phone home service is healthy"""
        response = self._make_request("/api/v1/status")
        return response is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the metrics client"""
        return {
            "is_registered": self.is_registered,
            "instance_id": self.instance_id,
            "is_running": self.running,
            "server_healthy": self.check_server_health(),
            "offline_data_count": len(self.offline_data),
            "app_identifier": self.app_identifier,
            "app_version": self.app_version,
            "server_url": self.server_url,
            "heartbeat_interval": self.heartbeat_interval,
            "analytics_enabled": not bool(self.system_info.get("analytics_disabled", False)),
            "system_info": self.system_info
        }

# Global instance
license_client = None
_initialization_lock = threading.Lock()

def init_license_client(app_identifier: str = "timetracker", app_version: str = "1.0.0") -> LicenseServerClient:
    """Initialize the global license client instance"""
    global license_client
    
    with _initialization_lock:
        if license_client is None:
            logger.info(f"Creating new license client instance (app: {app_identifier}, version: {app_version})")
            license_client = LicenseServerClient(app_identifier, app_version)
            logger.info(f"License client initialized (instance: {id(license_client)})")
        else:
            logger.info(f"License client already initialized, reusing existing instance (instance: {id(license_client)})")
    
    return license_client

def get_license_client() -> Optional[LicenseServerClient]:
    """Get the global license client instance"""
    return license_client

def start_license_client() -> bool:
    """Start the global license client"""
    global license_client
    
    if license_client is None:
        logger.error("License client not initialized")
        return False
    
    # Check if already running
    if license_client.running:
        logger.info("License client already running")
        return True
    
    return license_client.start()

def stop_license_client():
    """Stop the global license client"""
    global license_client
    
    if license_client:
        license_client.stop()

def send_usage_event(event_type: str, event_data: Dict[str, Any] = None):
    """Send a usage event to the metrics server"""
    if not license_client:
        return False
        
    data_point = {
        "key": "usage_event",
        "value": event_type,
        "type": "string",
        "metadata": event_data or {}
    }
    
    return license_client.send_usage_data([data_point])

