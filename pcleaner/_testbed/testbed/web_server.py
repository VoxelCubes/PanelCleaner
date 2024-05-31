# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/web_server.ipynb.

# %% ../nbs/web_server.ipynb 1
from __future__ import annotations


# %% auto 0
__all__ = ['display_ngrok_warning', 'WebServer', 'setup_ngrok', 'WebServerStdlib', 'WebServerBottle']

# %% ../nbs/web_server.ipynb 12
import getpass
import http.server
import os
import signal
import socketserver
import threading
import uuid
from http import HTTPStatus
from pathlib import Path
from typing import Protocol

import portpicker
import psutil
import requests
import rich
from IPython.display import display
from IPython.display import HTML
from loguru import logger
from pyngrok import conf
from pyngrok import ngrok
from rich.console import Console

from .bottle import Bottle
from .bottle import HTTPError
from .bottle import response
from .bottle import run
from .bottle import static_file


# %% ../nbs/web_server.ipynb 17
console = Console(width=104, tab_size=4, force_jupyter=True)
cprint = console.print


# %% ../nbs/web_server.ipynb 18
def display_ngrok_warning(url):
    did = 'ngrokFrame' + str(uuid.uuid4())
    html_code = f"""
<div style="font-size: 13pt;" id="{did}">
  <div style="background-color: aliceblue;">
    <p><b>Ngrok</b> displays a <b>warning page</b> as a security measure to prevent unintentional access to your local servers. This page requires you to <b>confirm</b> that you wish to proceed to the content.</p>
    <p style="font-weight: bold;">Please review the <em>ngrok</em> warning page displayed below. If prompted, click '<b>Visit Page</b>' to proceed.</p>
    Don't worry if you see a <b>404</b> or <b>403</b> error. Then, you can click the '<b>Close</b>' button below to hide this section.</p>
  </div>
    <iframe src="{url}" width="100%" height="600px" style="border:none;"></iframe>
    <button onclick="document.getElementById('{did}').innerHTML='';">Close</button>
</div>
"""

    display(HTML(html_code))


# %% ../nbs/web_server.ipynb 19
class WebServer(Protocol):
    @property
    def public_url(self) -> str | None: ...
    @property
    def unc_share(self) -> Path | None: ...
    @property
    def prefix(self) -> str: ...
    @property
    def running(self) -> bool: ...
    def __init__(self, directory: Path | str = ""): ...
    def start(self): ...
    def stop(self): ...


def setup_ngrok(server_cls: type[WebServer], images_dir: str | Path):
    cprint(
        "Enter your ngrok authtoken, which can be copied from "
        "https://dashboard.ngrok.com/get-started/your-authtoken"
    )
    auth_token = getpass.getpass()
    conf.get_default().auth_token = auth_token
    ngrok.set_auth_token(auth_token)

    server = server_cls(directory=str(images_dir))
    try:
        server.start()
    except Exception as e:
        cprint(f"Error starting server: {e}")
        return None

    display_ngrok_warning(f"{server.public_url}/{server.prefix}/pcleaner.png")
    return server


# %% ../nbs/web_server.ipynb 24
class ImageHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        for k,v in {
                'ngrok-skip-browser-warning': 'true',
                'User-Agent': 'MyCustomUserAgent/1.0',
                'Cache-Control': 'public, max-age=86400'
            }.items():
            self.send_header(k, v)
        super().end_headers()

    def do_GET(self):
        if self.is_image_request(self.path):
            super().do_GET()
        else:
            self.send_error(HTTPStatus.FORBIDDEN, "Only image files are accessible.")

    def is_image_request(self, path):
        allowed_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
        _, ext = os.path.splitext(path)
        return ext.lower() in allowed_extensions
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=self.directory, **kwargs)


# %% ../nbs/web_server.ipynb 25
class WebServerStdlib:
    """
    A simple web server for serving images from a local directory using http.server and ngrok.
    
    It is intended to be used in environments like Google Colab, where direct
    web server hosting might not be feasible. It uses ngrok to allow images to be accessed 
    via a public URL.
    
    Attributes:
        directory (str): The directory from which files are served.
        port (int): The local port on which the server listens.
        public_url (str): The ngrok public URL where the server is accessible.
        tunnel (ngrok.NgrokTunnel): The ngrok tunnel object.
    
    Methods:
        start(): Starts the web server and the ngrok tunnel.
        stop(): Stops the web server and disconnects the ngrok tunnel.
        make_request(path="/"): Makes a request to the ngrok URL to fetch data from the server.
    """
    
    def __init__(self, directory: Path | str=""):
        port = portpicker.pick_unused_port()
        self.port = port
        if isinstance(directory, str): 
            directory = Path(directory)
        assert directory.exists(), f"Directory {directory} does not exist"
        self.directory = str(directory.resolve())
        self.thread = None
        self.httpd = None
        self.public_url = None
        self.prefix = ''
        self.unc_share = None
        self.tunnel = None

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()
    
    def start_server(self):
        Handler = ImageHTTPRequestHandler 
        Handler.directory = self.directory
        try:
            with socketserver.TCPServer(("", self.port), Handler) as httpd:
                self.httpd = httpd
                httpd.serve_forever()
        except OSError as e:
            cprint(f"Error: {e}")

    def start(self):
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.start_server)
            self.thread.start()
            self.tunnel = ngrok.connect(self.port)  # type: ignore
            self.public_url = self.tunnel.public_url
            if self.public_url is not None:
                self.unc_share = Path(self.public_url.replace('https:', ''))
            cprint(f"ngrok tunnel: {self.tunnel}")
            cprint(f"Public URL: {self.public_url}")
        else:
            cprint("Server is already running")

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        if self.tunnel and self.tunnel.public_url:
            ngrok.disconnect(self.tunnel.public_url)  # Use the stored tunnel object's URL
            cprint("Ngrok tunnel disconnected")
            ngrok.kill()
        if self.thread:
            self.thread.join()
        self.thread = self.public_url = self.unc_share = None
        cprint("Server stopped")

    def make_request(self, path="/"):
        """Makes a request to the ngrok URL with headers to bypass the ngrok warning."""
        if self.public_url:
            url = f"{self.public_url}{path}"
            headers = {
                "ngrok-skip-browser-warning": "true",
                "User-Agent": "MyCustomUserAgent/1.0"
            }
            response = requests.get(url, headers=headers)
            return response.text
        else:
            return "Server not started or public URL not available."

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# %% ../nbs/web_server.ipynb 39
app = Bottle()

@app.route('/images/<filename:path>')  # type: ignore
def serve_image(filename):
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        return HTTPError(404, "File not found")
    response.set_header('Cache-Control', 'public, max-age=86400')  # Set caching headers
    return static_file(filename, root=app.config['image_dir'])

@app.route('/shutdown')  # type: ignore
def shutdown():
    current_process = psutil.Process()
    current_process.send_signal(signal.SIGTERM)


# %% ../nbs/web_server.ipynb 40
class WebServerBottle:
    """
    A simple web server for serving images from a local directory using ngrok.
    This class uses the Bottle framework to handle HTTP requests and ngrok to expose the 
    server to the internet.It is designed to be used in environments like Google Colab, 
    where direct web server hosting might not be feasible.
    
    Attributes:
        directory (Path | str): The directory from which files are served.
        port (int): The local port on which the server listens.
        public_url (str): The ngrok public URL where the server is accessible.
        tunnel (ngrok.NgrokTunnel): The ngrok tunnel object.
    
    Methods:
        start(): Starts the web server and the ngrok tunnel.
        stop(): Stops the web server and disconnects the ngrok tunnel.
    """
    
    def __init__(self, directory: Path | str = ""):
        self.port = portpicker.pick_unused_port()
        if isinstance(directory, str):
            directory = Path(directory)
        assert directory.exists(), f"Directory {directory} does not exist"
        self.directory = directory
        self.thread = None
        self.httpd = None
        self.public_url = None
        self.unc_share = None
        self.prefix = 'images'
        self.tunnel = None
        app.config['image_dir'] = str(directory)  # directory for Bottle
        # app.routes[0].callback.__globals__['image_dir'] = str(directory)  # directory for Bottle

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start_server(self):
        def bottle_run():
            run(app, host='localhost', port=self.port)
        
        self.thread = threading.Thread(target=bottle_run)
        self.thread.start()
        self.tunnel = ngrok.connect(self.port)  # type: ignore
        self.public_url = self.tunnel.public_url
        if self.public_url is not None:
            self.unc_share = Path(self.public_url.replace('https:', ''))/self.prefix
        cprint(f"ngrok tunnel: {self.tunnel}")
        cprint(f"Public URL: {self.public_url}")

    def start(self):
        if self.thread is None or not self.thread.is_alive():
            self.start_server()
        else:
            cprint("Server is already running")

    def stop(self):
        if self.tunnel and self.tunnel.public_url:
            ngrok.disconnect(self.tunnel.public_url)
            cprint("Ngrok tunnel disconnected")
            ngrok.kill()
        
        if self.thread:
            self.make_request('/shutdown')
            self.thread.join(timeout=10)
            if self.thread.is_alive():
                print("Thread did not terminate, proceeding with forceful shutdown.")
            else:
                print("Server thread stopped successfully.")
        self.thread = self.tunnel = self.public_url = self.unc_share = None
        cprint("Server stopped")

    def make_request(self, path="/"):
        """Makes a request to the ngrok URL with headers to bypass the ngrok warning."""
        if self.public_url:
            url = f"{self.public_url}{path}"
            headers = {
                "ngrok-skip-browser-warning": "true",
                "User-Agent": "MyCustomUserAgent/1.0"
            }
            response = requests.get(url, headers=headers)
            return response.text
        else:
            return "Server not started or public URL not available."

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

