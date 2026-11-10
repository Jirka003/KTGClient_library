from pathlib import Path


class HelpFuncs:
    
    @staticmethod
    def txt_to_list(file: Path) -> list:
        """Takes a text file and returns list"""
        new_list = []
        try:
            with open(file, "r") as f:
                for line in f:
                    line = line.strip()
                    new_list.append(line)
        except FileNotFoundError:
            print("File does not exists")
            return None
        
        return new_list
    
    @staticmethod
    def save_as(content, name: str):
        """Writes content to a file"""
        content = str(content)
        try:
            with open(name, "a") as f:
                f.write(content)
        except Exception as e:
            print(f"Error {e}")
            
        
        