import sys
import os
from interface.blm.db import BLMDatabase
from interface.blm.exporter import MermaidExporter

def main():
    db_path = "data/blm.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} not found.")
        sys.exit(1)
        
    db = BLMDatabase(db_path)
    exporter = MermaidExporter(db)
    
    print("--- BLM State Graph (Mermaid) ---")
    print(exporter.export())
    print("---------------------------------")
    print("\nCopy-paste the output above into https://mermaid.live/ to visualize.")

if __name__ == "__main__":
    main()
