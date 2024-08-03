import http.server
import socketserver
import socket
import threading
import os
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import json
from pymongo import MongoClient

PORT = 3000
SOCKET_PORT = 5000

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "index.html"
        elif self.path == "/message":
            self.path = "message.html"
        elif self.path == "/style.css":
            self.path = "style.css"
        elif self.path == "/logo.png":
            self.path = "logo.png"
        else:
            self.path = "error.html"
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open("error.html", "rb") as file:
                self.wfile.write(file.read())
            return
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        if self.path == "/submit":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = parse_qs(post_data.decode('utf-8'))
            message = {
                "date": str(datetime.now()),
                "username": data["username"][0],
                "message": data["message"][0]
            }
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', SOCKET_PORT))
                s.sendall(json.dumps(message).encode('utf-8'))
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()

def run_http_server():
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

def run_socket_server():
    client = MongoClient("mongodb://mongo:27017/")
    db = client["messages_db"]
    collection = db["messages"]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('', SOCKET_PORT))
        server_socket.listen()
        print(f"Socket server listening on port {SOCKET_PORT}")
        while True:
            conn, addr = server_socket.accept()
            with conn:
                print('Connected by', addr)
                data = conn.recv(1024)
                if data:
                    message = json.loads(data.decode('utf-8'))
                    collection.insert_one(message)
                    print(f"Message saved: {message}")

if __name__ == "__main__":
    threading.Thread(target=run_http_server).start()
    threading.Thread(target=run_socket_server).start()
