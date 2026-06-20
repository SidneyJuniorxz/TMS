import sys
import os
import uvicorn

# Ensure the project root is in the python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)
