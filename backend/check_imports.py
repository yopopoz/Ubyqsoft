try:
    print("Importing fastapi...")
    from fastapi import FastAPI
    print("Importing app.main...")
    from app.main import app
    print("Import successful!")
except Exception as e:
    print(f"Import failed: {e}")
