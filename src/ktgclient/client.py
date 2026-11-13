# This library is build on HTTP/1.1, so please remember that, while creating a project with it. Im just high-school student, I know its not gonna be perfect.

import socket
import ssl
import sys
import json
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.parse import urljoin

RESET = "\033[0m"
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

from .response import Response

class KTGHttpError(Exception):
    """Errors and stuff"""
    pass

class KTGClient:
    """Everything works via HTTP 1.1"""
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
                
            headers_raw, body_buffer = responce_bytes.split(b"\r\n\r\n", 1)
            
            headers_text = headers_raw.decode("utf-8", errors="ignore")
            content_length = 0
            for line in headers_text.split("\r\n"):
                if line.lower().startswith("content-length"):
                    content_length = int(line.split(":")[1].strip())
            
            body_data = body_buffer
            while len(body_data) < content_length:
                needed = content_length - len(body_data)
                chunk = secure_socket.recv(min(needed, 4096))
                if not chunk:
                    break
                body_data += chunk
            
        except socket.timeout:
            raise KTGHttpError("Connection timeout")
        finally:
            secure_socket.close()
        
        full_responce_bytes = headers_raw + b"\r\n\r\n" + body_data
        responce_text = full_responce_bytes.decode("utf-8", errors="ignore")
        
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
                
            headers_raw, body_buffer = responce_bytes.split(b"\r\n\r\n", 1)
            
            headers_text = headers_raw.decode("utf-8", errors="ignore")
            content_length = 0
            for line in headers_text.split("\r\n"):
                if line.lower().startswith("content-length"):
                    content_length = int(line.split(":")[1].strip())
            
            body_data = body_buffer
            while len(body_data) < content_length:
                needed = content_length - len(body_data)
                chunk = secure_socket.recv(min(needed, 4096))
                if not chunk:
                    break
                body_data += chunk
        except socket.timeout:
            raise KTGHttpError("Connection timeout")
        finally:
            secure_socket.close()
        
        full_responce_bytes = headers_raw + b"\r\n\r\n" + body_data
        responce_text = full_responce_bytes.decode("utf-8", errors="ignore")

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
                
            headers_raw, body_buffer = responce_bytes.split(b"\r\n\r\n", 1)
            
            headers_text = headers_raw.decode("utf-8", errors="ignore")
            content_length = 0
            for line in headers_text.split("\r\n"):
                if line.lower().startswith("content-length"):
                    content_length = int(line.split(":")[1].strip())
            
            body_data = body_buffer
            while len(body_data) < content_length:
                needed = content_length - len(body_data)
                chunk = secure_socket.recv(min(needed, 4096))
                if not chunk:
                    break
                body_data += chunk
                
        except socket.timeout:
            raise KTGHttpError("Connection timeout while reading data from server")
        finally:
            secure_socket.close()
        
        full_responce_bytes = headers_raw + b"\r\n\r\n" + body_data
        responce_text = full_responce_bytes.decode("utf-8", errors="ignore")

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
                
            headers_raw, body_buffer = responce_bytes.split(b"\r\n\r\n", 1)
            
            headers_text = headers_raw.decode("utf-8", errors="ignore")
            content_length = 0
            for line in headers_text.split("\r\n"):
                if line.lower().startswith("content-length"):
                    content_length = int(line.split(":")[1].strip())
            
            body_data = body_buffer
            while len(body_data) < content_length:
                needed = content_length - len(body_data)
                chunk = secure_socket.recv(min(needed, 4096))
                if not chunk:
                    break
                body_data += chunk
        except socket.timeout:
            raise KTGHttpError("Connection timeout while reading data from server")
        finally:
            secure_socket.close()
        
        full_responce_bytes = headers_raw + b"\r\n\r\n" + body_data
        responce_text = full_responce_bytes.decode("utf-8", errors="ignore")

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
                
            headers_raw, body_buffer = responce_bytes.split(b"\r\n\r\n", 1)
            
            headers_text = headers_raw.decode("utf-8", errors="ignore")
            content_length = 0
            for line in headers_text.split("\r\n"):
                if line.lower().startswith("content-length"):
                    content_length = int(line.split(":")[1].strip())
            
            body_data = body_buffer
            while len(body_data) < content_length:
                needed = content_length - len(body_data)
                chunk = secure_socket.recv(min(needed, 4096))
                if not chunk:
                    break
                body_data += chunk
        except socket.timeout:
            raise KTGHttpError("Connection timeout")
        finally:
            secure_socket.close()
        
        full_responce_bytes = headers_raw + b"\r\n\r\n" + body_data
        responce_text = full_responce_bytes.decode("utf-8", errors="ignore")

        return Response(responce_text)
    
   ###################### HEAD 
    def ktg_head(self, url: str, headers: dict = None):
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
                f"HEAD {directory} HTTP/1.1\r\n"
                f"Host: {domain}\r\n"
                f"{headers_data}"
                "\r\n"  
            )  
        else:
            domain = parsed 
            request_delete = (
                f"HEAD / HTTP/1.1\r\n"
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
                
            headers_raw, body_buffer = responce_bytes.split(b"\r\n\r\n", 1)
            
            headers_text = headers_raw.decode("utf-8", errors="ignore")
            content_length = 0
            for line in headers_text.split("\r\n"):
                if line.lower().startswith("content-length"):
                    content_length = int(line.split(":")[1].strip())
            
            body_data = body_buffer
            while len(body_data) < content_length:
                needed = content_length - len(body_data)
                chunk = secure_socket.recv(min(needed, 4096))
                if not chunk:
                    break
                body_data += chunk
        except socket.timeout:
            raise KTGHttpError("Connection timeout")
        finally:
            secure_socket.close()
        
        full_responce_bytes = headers_raw + b"\r\n\r\n" + body_data
        responce_text = full_responce_bytes.decode("utf-8", errors="ignore")

        return Response(responce_text)
    
######################## OPTIONS
    def ktg_options(self, url: str, headers: dict = None):
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
                f"OPTIONS {directory} HTTP/1.1\r\n"
                f"Host: {domain}\r\n"
                f"{headers_data}"
                "\r\n"  
            )  
        else:
            domain = parsed 
            request_delete = (
                f"OPTIONS / HTTP/1.1\r\n"
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
                
            headers_raw, body_buffer = responce_bytes.split(b"\r\n\r\n", 1)
            
            headers_text = headers_raw.decode("utf-8", errors="ignore")
            content_length = 0
            for line in headers_text.split("\r\n"):
                if line.lower().startswith("content-length"):
                    content_length = int(line.split(":")[1].strip())
            
            body_data = body_buffer
            while len(body_data) < content_length:
                needed = content_length - len(body_data)
                chunk = secure_socket.recv(min(needed, 4096))
                if not chunk:
                    break
                body_data += chunk
        except socket.timeout:
            raise KTGHttpError("Connection timeout")
        finally:
            secure_socket.close()
        
        full_responce_bytes = headers_raw + b"\r\n\r\n" + body_data
        responce_text = full_responce_bytes.decode("utf-8", errors="ignore")

        return Response(responce_text)
    
    
######################## FUZZ
    @staticmethod
    def ktg_simple_fuzz(base_url: str, wordlist: list, exclude_status_codes: list = None, match_status_code: list = None, exclude_size: list = None, threads: int = 1):
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
    
    @staticmethod        
    def support_crawl_grep_href(url: str):
        client = KTGClient()
        response = client.ktg_get(url)
        text = response.text
        links = []
        
        def handle_tag(tag, atributes):
            if tag == "a":
                for name, value in atributes:
                    if name == "href" and value:
                        links.append(urljoin(url, value))
        
        parser = HTMLParser()
        parser.handle_starttag = handle_tag
        parser.feed(text)
        return links
    
    @staticmethod   
    def ktg_simple_crawl(start_url: str, max_pages: int = 20):
        visited = set()
        to_visit = [start_url]
        all_links = []
        
        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)
            
            if url in visited:
                continue
            visited.add(url)
            
            links = KTGClient.support_crawl_grep_href(url)
            all_links.extend(links)
            
            for link in links:
                if link not in visited:
                    to_visit.append(link)
        
        return all_links
    
############################### 403 bypasser 
    @staticmethod
    def ktg_simple_403_bypasser(url: str, change_request_method: bool = False, path_manipulation: bool = False, header_spoofing: bool = False):
        client = KTGClient()
        r = client.ktg_get(url=url)
        
        if r.status_code != 403:
            print("This site does not return 403, ending the program")
            sys.exit()
        
        if change_request_method is True:
            methods = ["ktg_get", "ktg_post", "ktg_put", "ktg_patch", "ktg_delete", "ktg_head", "ktg_options"]
            for method in methods:
                current_method = getattr(client, method)
                r = current_method(url)
                
                if r.status_code == 403:
                    continue
                
                if r.status_code in range(200, 300):
                    print(f"{GREEN}Status code: {r.status_code} | Method: {current_method}{RESET} | Size: {len(r.text)}")
                    
                elif r.status_code in range(300, 406):
                    print(f"{BLUE}Status code: {r.status_code} | Method: {current_method}{RESET} | Size: {len(r.text)}")        
                    
        if path_manipulation is True:
            new_url = ""
            if url.startswith("https://"):
                new_url = url.replace("https://", "")
            elif url.startswith("http://"):
                new_url = url.replace("http://", "")
            else:
                print("Invalid url")
                sys.exit()
                
            current_method = getattr(client, "ktg_get")
            
            if "/" in new_url:
                directories = url.split("/")
                path = directories[-1]  ##### https://example.com/dir -> [example.com, dir] -> dir 
                manipulation_methods = [f"/{path}/", f"{path}../", f"/./{path}../", f"//{path}", f"/{path}//", f"/./{path}", f"/{path}/./", f"/{path}/../{path}", f"/;/{path}",f"/{path}%2e%2e%2f", f"/%252f{path}", f"/{path}#", f"/{path}?"]
                
                for method in manipulation_methods:
                    directories[-1] = method
                    url_to_send = "/".join(directories)
                    r = current_method(url_to_send)
                    
                    if r.status_code == 403:
                        continue
                    
                    if r.status_code in range(200, 300):
                        print(f"{GREEN}Status code: {r.status_code} | Url: {url_to_send} | Size: {len(r.text)}{RESET}")
                    
                    elif r.status_code in range(300, 406):
                        print(f"{BLUE}Status code: {r.status_code} | Url: {url_to_send} | Size: {len(r.text)}{RESET}")
                    
            else:
                print("You need to enter a directory (example: https://example.com/path_to_manipulate)")
                sys.exit()
        
        if header_spoofing is True:
            client_header_spoofing = KTGClient()
            
            header_spoof_dict = {
                "X-Forwarded-For": "127.0.0.1",
                "X-Real-IP": "127.0.0.1",    
                "X-Originating-IP": "127.0.0.1",
                "X-Remote-IP": "127.0.0.1",
                "X-Client-IP": "127.0.0.1",
                "True-Client-IP": "127.0.0.1",
                "X-Custom-IP-Authorization": "127.0.0.1",
                "X-Rewrite-URL": "/admin",
                "X-Original-URL": "/admin"
            }
            
            for header, ip in header_spoof_dict.items():
                r = client_header_spoofing.ktg_get(url, headers={header: ip})
                if r.status_code == 403:
                    continue
                    
                if r.status_code in range(200, 300):
                    print(f"{GREEN}Status code: {r.status_code} | Url: {url_to_send} | Size: {len(r.text)}{RESET}")
                    
                elif r.status_code in range(300, 406):
                    print(f"{BLUE}Status code: {r.status_code} | Url: {url_to_send} | Size: {len(r.text)}{RESET}")

                
            
            

                
                
                
        
