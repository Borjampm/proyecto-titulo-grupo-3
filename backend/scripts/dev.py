# dev.py
def main():
    import uvicorn
    uvicorn.run("app.main:app", reload=True, host="0.0.0.0", port=8000)