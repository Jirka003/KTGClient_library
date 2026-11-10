import socket
import ssl
import sys
import json
from concurrent.futures import ThreadPoolExecutor

from .response import Response

class KTGHttpError(Exception):
    """Errors and stuff"""
    pass

class KTGClient:
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
    
    @staticmethod
    def parse(url: str):
        new_url = ""
        if url.startswith("https://"):
            new_url = url.replace("https://", "")
        elif url.startswith("http://"):
            new_url = url.replace("http://", "")
        else:
            print("Invalid url")
            sys.exit()
        if "/" in new_url:
            domain, directory = new_url.split("/", 1)
            return domain, "/" + directory
        else:
            return new_url
        
    def create_secure_socket(self, domain):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.timeout)
        except socket.error as err:
            raise KTGHttpError(f"Error while creating a socket: {err}")
            
        port = 443

        try:
            host_ip = socket.gethostbyname(domain)
        except socket.gaierror as err:
            raise KTGHttpError(f"Connection failed: {err}")
            
        try:
            s.connect((host_ip, port))
        except (socket.timeout, ConnectionRefusedError) as err:
            raise KTGHttpError(f"Connecting to {domain}:{port} failed: {err}") 

        try:
            content = ssl.create_default_context()
            secure_socket = content.wrap_socket(s, server_hostname=domain)   
        except ssl.SSLError as err:
            raise KTGHttpError(f"Error of SSL handshake for {domain}: {err}")
        
        return secure_socket
    
################################# GET

    def ktg_get(self, url: str, headers: dict = None):
        parsed = self.parse(url)
        
        if headers is None:
            headers = {}
        
        must_have_headers = {"User-Agent": "KTG/1.0", "Connection": "close"}
        must_have_headers.update(headers)
            
        header_list = []
        for key, value in must_have_headers.items():
            header_list.append(f"{key}: {value}\r\n")
            
        headers_data = "".join(header_list)
        
        if isinstance(parsed, tuple):
            domain, directory = parsed
            request_get = (
                f"GET {directory} HTTP/1.1\r\n"
                f"Host: {domain}\r\n"
                f"{headers_data}"
                "\r\n"
            ) 
        else:
            domain = parsed 
            request_get = (
                "GET / HTTP/1.1\r\n"
                f"Host: {domain}\r\n"
                f"{headers_data}"
                "\r\n"
            )

        secure_socket = self.create_secure_socket(domain) 
        
        try:
            secure_socket.sendall(request_get.encode("utf-8"))
            
            responce_bytes = b""
            while True:
                chunk = secure_socket.recv(4096)
                if not chunk:
                    break
                responce_bytes += chunk
        except socket.timeout:
            raise KTGHttpError("Connection timeout")
        finally:
            secure_socket.close()
        
        responce_text = responce_bytes.decode("utf-8", errors="ignore")
        
        return Response(responce_text)
    
############################# POST

    def ktg_post(self, url: str, params: dict = None, headers: dict = None, json_data: dict = None):
        parsed = self.parse(url)
        
        default_content_type = "application/x-www-form-urlencoded"
        body_data = ""

        if json_data is not None:
            body_data = json.dumps(json_data)
            default_content_type = "application/json"
        elif params:
            param_list = []
            for key, value in params.items():
                param_list.append(f"{key}={value}")
            body_data = "&".join(param_list)

        if headers is None:
            headers = {}
        
        must_have_headers = {
            "User-Agent": "KTG/1.0", 
            "Content-Type": default_content_type, 
            "Content-Length": str(len(body_data.encode("utf-8"))),
            "Connection": "close"
        }
            
        must_have_headers.update(headers)

        header_list = []
        for key, value in must_have_headers.items():
            header_list.append(f"{key}: {value}\r\n")
        
        headers_data = "".join(header_list)             
        
        if isinstance(parsed, tuple):
            domain, directory = parsed
            request_post = (
                f"POST {directory} HTTP/1.1\r\n"
                f"Host: {domain}\r\n"
                f"{headers_data}"
                "\r\n"  
                f"{body_data}"
            )  
        else:
            domain = parsed 
            request_post = (
                f"POST / HTTP/1.1\r\n"
                f"Host: {domain}\r\n"
                f"{headers_data}"
                "\r\n"  
                f"{body_data}"
            )
    
        secure_socket = self.create_secure_socket(domain) 
        
        try:
            secure_socket.sendall(request_post.encode("utf-8"))
            
            responce_bytes = b""
            while True:
                chunk = secure_socket.recv(4096)
                if not chunk:
                    break
                responce_bytes += chunk
        except socket.timeout:
            raise KTGHttpError("Connection timeout")
        finally:
            secure_socket.close()
        
        responce_text = responce_bytes.decode("utf-8", errors="ignore")
        return Response(responce_text)

##################### PUT

    def ktg_put(self, url: str, params: dict = None, headers: dict = None, json_data: dict = None):
        parsed = self.parse(url)
        
        default_content_type = "application/x-www-form-urlencoded"
        body_data = ""

        if json_data is not None:
            body_data = json.dumps(json_data)
            default_content_type = "application/json"
        elif params:
            param_list = []
            for key, value in params.items():
                param_list.append(f"{key}={value}")
            body_data = "&".join(param_list)

        if headers is None:
            headers = {}
        
        must_have_headers = {
            "User-Agent": "KTG/1.0", 
            "Content-Type": default_content_type, 
            "Content-Length": str(len(body_data.encode("utf-8"))),
            "Connection": "close"
        }
            
        must_have_headers.update(headers)

        header_list = []
        for key, value in must_have_headers.items():
            header_list.append(f"{key}: {value}\r\n")
        
        headers_data = "".join(header_list)     

        if isinstance(parsed, tuple):
            domain, directory = parsed
            request_put = (
                f"PUT {directory} HTTP/1.1\r\n"
                f"Host: {domain}\r\n"
                f"{headers_data}"
                "\r\n"  
                f"{body_data}"
            )  
        else:
            domain = parsed 
            request_put = (
                f"PUT / HTTP/1.1\r\n"
                f"Host: {domain}\r\n"
                f"{headers_data}"
                "\r\n"  
                f"{body_data}"
            )

        secure_socket = self.create_secure_socket(domain) 
        
        try:
            secure_socket.sendall(request_put.encode("utf-8"))
            
            responce_bytes = b""
            while True:
                chunk = secure_socket.recv(4096)
                if not chunk:
                    break
                responce_bytes += chunk
        except socket.timeout:
            raise KTGHttpError("Connection timeout while reading data from server")
        finally:
            secure_socket.close()
        
        responce_text = responce_bytes.decode("utf-8", errors="ignore")
        return Response(responce_text)
    
################### PATCH

    def ktg_patch(self, url: str, params: dict = None, headers: dict = None, json_data: dict = None):
        parsed = self.parse(url)
        
        default_content_type = "application/x-www-form-urlencoded"
        body_data = ""

        if json_data is not None:
            body_data = json.dumps(json_data)
            default_content_type = "application/json"
        elif params:
            param_list = []
            for key, value in params.items():
                param_list.append(f"{key}={value}")
            body_data = "&".join(param_list)
            
        if headers is None:
            headers = {}
        
        must_have_headers = {
            "User-Agent": "KTG/1.0", 
            "Content-Type": default_content_type, 
            "Content-Length": str(len(body_data.encode("utf-8"))),
            "Connection": "close"
        }
            
        must_have_headers.update(headers)

        header_list = []
        for key, value in must_have_headers.items():
            header_list.append(f"{key}: {value}\r\n")
        
        headers_data = "".join(header_list)     
        
        if isinstance(parsed, tuple):
            domain, directory = parsed
            request_patch = (
                f"PATCH {directory} HTTP/1.1\r\n"
                f"Host: {domain}\r\n"
                f"{headers_data}"
                "\r\n" 
                f"{body_data}"
            )  
        else:
            domain = parsed 
            request_patch = (
                f"PATCH / HTTP/1.1\r\n"
                f"Host: {domain}\r\n"
                f"{headers_data}"
                "\r\n"  
                f"{body_data}"
            )

        secure_socket = self.create_secure_socket(domain) 
        
        try:
            secure_socket.sendall(request_patch.encode("utf-8"))
            
            responce_bytes = b""
            while True:
                chunk = secure_socket.recv(4096)
                if not chunk:
                    break
                responce_bytes += chunk
        except socket.timeout:
            raise KTGHttpError("Connection timeout while reading data from server")
        finally:
            secure_socket.close()
        
        responce_text = responce_bytes.decode("utf-8", errors="ignore")
        return Response(responce_text)
    
####################### DELETE

    def ktg_delete(self, url: str, headers: dict = None):
        parsed = self.parse(url)

        must_have_headers = {"User-Agent": "KTG/1.0", "Connection": "close"}
        if headers is None:
            headers = {}
        must_have_headers.update(headers)
        
        header_list = []
        for key, value in must_have_headers.items():
            header_list.append(f"{key}: {value}\r\n")
            
        headers_data = "".join(header_list)
        
        if isinstance(parsed, tuple):
            domain, directory = parsed
            request_delete = (
                f"DELETE {directory} HTTP/1.1\r\n"
                f"Host: {domain}\r\n"
                f"{headers_data}"
                "\r\n"  
            )  
        else:
            domain = parsed 
            request_delete = (
                f"DELETE / HTTP/1.1\r\n"
                f"Host: {domain}\r\n"
                f"{headers_data}"
                "\r\n"  
            )
    
        secure_socket = self.create_secure_socket(domain) 
        
        try:
            secure_socket.sendall(request_delete.encode("utf-8"))
            
            responce_bytes = b""
            while True:
                chunk = secure_socket.recv(4096)
                if not chunk:
                    break
                responce_bytes += chunk
        except socket.timeout:
            raise KTGHttpError("Connection timeout")
        finally:
            secure_socket.close()
        
        responce_text = responce_bytes.decode("utf-8", errors="ignore")
        return Response(responce_text)
    
######################## FUZZ
    @staticmethod
    def ktg_fuzz(base_url: str, wordlist: list, exclude_status_codes: list = None, match_status_code: list = None, exclude_size: list = None, threads: int = 1):
        if not "FUZZ" in base_url:
            print("Missing keyword FUZZ in url")
            sys.exit()
        
        if exclude_status_codes is not None:
            exclude_status_codes = exclude_status_codes
        else:
            exclude_status_codes = []
            
        if match_status_code is not None:
            match_status_code = match_status_code
        else:
            match_status_code = range(200, 600)
        
        if exclude_size is not None:
            exclude_size = exclude_size
        else:
            exclude_size = [-1]
        
        def worker(word):   
            url = base_url.replace("FUZZ", word)
            try:
                client = KTGClient().ktg_get(url=url)
                
                if client is None:
                    return 
                
                if client.status_code == 404 or client.status_code in exclude_status_codes or len(client.text) in exclude_size:
                    return 
                
                if client.status_code in match_status_code:
                    print(f"Status code: {client.status_code} | URL: {url} | Size: {len(client.text)}")
                
            except Exception:
                pass
                
                    
        with ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(worker, wordlist)
        
            
            
            
        
