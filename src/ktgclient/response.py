import json

class Response:
    def __init__(self, raw_data: str):
        self.raw_data = raw_data
        self.status_code = self._extract_status_code(raw_data)
        self.text = self._extract_body(raw_data)
        self.headers_dict = self._extract_headers(raw_data)
        self.json_dict = self._json()
    

    def _json(self):
        try:
            return json.loads(self.text)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _extract_status_code(data):
        try:
            first_line = data.split("\r\n")[0]
            return int(first_line.split(" ")[1])
        except:
            return None

    @staticmethod
    def _extract_body(data: str):
        parts = data.split("\r\n\r\n", 1)
        if len(parts) > 1: 
            return parts[1] 
        else:
            return ""
    
    @staticmethod
    def _extract_headers(data: str):
        headers_dict = {}
        parts = data.split("\r\n\r\n", 1)
        header_lines = parts[0].split("\r\n")
        
        for line in header_lines:
            if not line.startswith("HTTP"):
                
                key, value = line.split(":", 1)
                headers_dict[key] = value
        
        return headers_dict
    

        
        
              



