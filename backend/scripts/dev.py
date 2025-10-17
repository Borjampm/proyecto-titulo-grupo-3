# dev.py
def main():
    import uvicorn
    uvicorn.run("app.main:app", reload=True)