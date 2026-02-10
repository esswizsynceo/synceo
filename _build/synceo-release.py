import os
import sys
import socket
import uuid
import logging
from waitress import serve
from logging.handlers import RotatingFileHandler
from flask import Flask, request, send_file, jsonify
from zeroconf import ServiceInfo, Zeroconf
import threading
import pystray
from PIL import Image
import time
from pystray import MenuItem as item, Menu
import subprocess


# -------------------------
# Resource helper
# -------------------------
def resource_path(relative):
	try:
		return os.path.join(sys._MEIPASS, relative)
	except Exception:
		return os.path.join(os.path.abspath("."), relative)
		

# -------------------------
# Detect base directory
# -------------------------
def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()

# -------------------------
# Logging
# -------------------------
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "synceo.log")

logger = logging.getLogger("synceo")
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(LOG_FILE, maxBytes=2*1024*1024, backupCount=5, encoding="utf-8")
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# -------------------------
# Flask App
# -------------------------
app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "shared_files")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def open_shared_files(icon=None, item=None):
	try:
		os.makedirs(UPLOAD_FOLDER, exist_ok=True)
		subprocess.Popen(["explorer", UPLOAD_FOLDER])
	except Exception as e:
		logger.error(f"Unable to open shared files folder: {e}")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file part", 400
    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)
    size_kb = os.path.getsize(save_path) // 1024
    logger.info(f"Upload: {save_path} ({size_kb} KB)")
    return {"status": "ok", "filename": file.filename}

@app.route("/files", methods=["GET"])
def list_files():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]
    logger.info(f"Filelist requested: {len(files)} files")
    return jsonify(files)

@app.route("/download/<path:file_name>", methods=["GET"])
def download_file(file_name):
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    if not os.path.exists(file_path):
        return {"error": "File not found"}, 404
    logger.info(f"Download: {file_path} ({os.path.getsize(file_path)//1024} KB)")
    return send_file(file_path, as_attachment=True, download_name=file_name, conditional=False, etag=False, max_age=0)

# -------------------------
#  LAN IP Server
# -------------------------
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

# -------------------------
# Zeroconf
# -------------------------
hostname = socket.gethostname()
short_id = uuid.uuid4().hex[:4]
service_name = f"{hostname}-{short_id}._http._tcp.local."

def start_zeroconf():
    try:
        ip = get_local_ip()
        desc = {"path": "/"}
        info = ServiceInfo(
            type_="_http._tcp.local.",
            name=service_name,
            addresses=[socket.inet_aton(ip)],
            port=5000,
            properties=desc
        )
        zeroconf = Zeroconf()
        zeroconf.register_service(info)
        logger.info(f"Zeroconf service registered: {service_name} on {ip}:5000")
        return zeroconf, info
    except Exception as e:
        logger.warning(f"Zeroconf service could not start: {e}")
        return None, None

# -------------------------
# Tray icon
# -------------------------
server_thread = None
zeroconf_service = None
zeroconf_info = None
server_running = False

def can_start():
	return not server_running

def can_stop():
	return server_running


def start_server(icon=None, item=None):
	global server_thread, zeroconf_service, zeroconf_info, server_running
	if server_running:
		logger.info("Server already running")
		return

	server_running = True
	zeroconf_service, zeroconf_info = start_zeroconf()

	def run_server():
		serve(app, host="0.0.0.0", port=5000)
		logger.info("Waitress server running on port 5000")

	server_thread = threading.Thread(target=run_server)
	server_thread.start()
	logger.info("Server thread started")
	
def start_server_action(icon, item):
	global server_running
	if server_running:
		return

	start_server()
	icon.update_menu()
	update_tray_icon(icon)
	server_running = True
	icon.update_menu()


def stop_server(icon=None, item=None):
    global server_running, zeroconf_service, zeroconf_info
    if not server_running:
        logger.info("Server not running")
        return
    server_running = False
    if zeroconf_service and zeroconf_info:
        zeroconf_service.unregister_service(zeroconf_info)
        zeroconf_service.close()
        logger.info("Zeroconf service stopped")
    logger.info("Server stopped")
	
def stop_server_action(icon, item):
	global server_running
	if not server_running:
		return

	stop_server()
	icon.update_menu()
	update_tray_icon(icon)

	server_running = False
	icon.update_menu()

	
def exit_app(icon, item):
	logger.info("Quit requested")
	stop_server()
	if icon:
		icon.visible = False
		icon.stop()			# close tray icon
	os._exit(0)				# Python exit


def create_tray():
	icon_start = Image.open(resource_path("icons/synceo_green.ico"))
	icon_stop  = Image.open(resource_path("icons/synceo_red.ico"))

	menu = pystray.Menu(
		item(
			"Start Synceo server",
			start_server_action,
			enabled=lambda item: can_start()
		),
		item(
			"Stop Synceo server",
			stop_server_action,
			enabled=lambda item: can_stop()
		),
		item(
			"My Shared Files",
			open_shared_files
		),
		pystray.Menu.SEPARATOR,
		item("Quit", exit_app)
	)

	icon = pystray.Icon(
		"Synceo",
		Image.open(resource_path("icons/synceo.ico")),
		"Synceo server",
		menu
	)

	icon.run()

def update_tray_icon(icon):
    if server_running:
        icon.icon = Image.open(resource_path("icons/synceo_green.ico"))
        icon.title = "Synceo — Server running"
    else:
        icon.icon = Image.open(resource_path("icons/synceo_red.ico"))
        icon.title = "Synceo — Server stopped"


# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    # starts tray in the main thread (block)
    create_tray()
