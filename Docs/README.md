# Documentation for developers

[env_format.txt](env_format.txt) for the .env file format.
[data.txt](data.txt) to see the table schemas that will be used in the database.
[features.txt](features.txt) just a to do list file to track the different features.

### Setting up
This codebase uses UV package installer. To setup and run the code:
```bash
pip install uv
uv sync
uv run main.py
```
Alternate method to run the program:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```
To add a new dependency:
```bash
uv add <dependency_name>
```
To remove an existing dependency:
```bash
uv remove <dependency_name>
```