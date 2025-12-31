#utilizing fast api 

from fastapi import FastAPI
#import the nba routes from app/api/nba_routes.py 
#that script holds all  api endpoints related to FETCHING nba games. list of games , list players that have props
from app.api.nba_routes import router as nba_router  

app = FastAPI(title="SharpEye Backend", version="0.1.0") #initialize the FastAPI app with a title and version

app.include_router(nba_router) #include the nba router to the main app, so all endpoints defined in nba_routes.py are accessible

@app.get("/health") #check if the api is running
def health():
    return {"status": "ok"} #return a simple json response indicating the service is operational


@app.get("/info") #root endpoint 
def info():
    return {"service": "SharpEye Backend", "version": "0.1.0"} #return basic info about the service

@app.get("/") #root endpoint   
def root():
    return {"message": "Welcome to the SharpEye Backend API"} #return a welcome message at the root endpoint 