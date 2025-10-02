#!/usr/bin/env python3
"""Convert dates in JSON files from DD/MM/YYYY or DD-MM-YYYY to YYYY-MM-DD."""

import json
import re
import argparse
from pathlib import Path
from datetime import datetime


def convert_date_string(date_str):
    """Convert DD/MM/YYYY or DD-MM-YYYY to YYYY-MM-DD."""
    # Try DD/MM/YYYY format
    match = re.match(r'(\d{2})/(\d{2})/(\d{4})', date_str)
    if match:
        day, month, year = match.groups()
        try:
            # Validate the date
            datetime(int(year), int(month), int(day))
            return f"{year}-{month}-{day}"
        except ValueError:
            return date_str
    
    # Try DD-MM-YYYY format
    match = re.match(r'(\d{2})-(\d{2})-(\d{4})', date_str)
    if match:
        day, month, year = match.groups()
        try:
            # Validate the date
            datetime(int(year), int(month), int(day))
            return f"{year}-{month}-{day}"
        except ValueError:
            return date_str
    
    return date_str


def convert_dates_in_object(obj):
    """Recursively convert dates in a JSON object."""
    if isinstance(obj, dict):
        return {key: convert_dates_in_object(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates_in_object(item) for item in obj]
    elif isinstance(obj, str):
        return convert_date_string(obj)
    else:
        return obj


def process_json_file(file_path):
    """Process a single JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        converted_data = convert_dates_in_object(data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=False, indent=2)
        
        print(f"Convertido: {file_path}")
        return True
    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert dates in JSON files to YYYY-MM-DD format")
    parser.add_argument("--file", "-f", help="Single JSON file to process")
    parser.add_argument("--dir", "-d", help="Directory to process recursively")
    args = parser.parse_args()
    
    if args.file:
        file_path = Path(args.file)
        if file_path.exists():
            process_json_file(file_path)
        else:
            print(f"Arquivo não encontrado: {file_path}")
    
    elif args.dir:
        dir_path = Path(args.dir)
        if dir_path.exists() and dir_path.is_dir():
            json_files = list(dir_path.rglob("*.json"))
            if not json_files:
                print("Nenhum arquivo JSON encontrado.")
                return
            
            success_count = 0
            for json_file in json_files:
                if process_json_file(json_file):
                    success_count += 1
            
            print(f"Processados com sucesso: {success_count}/{len(json_files)} arquivos")
        else:
            print(f"Diretório não encontrado: {dir_path}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
