# from fastapi import FastAPI
# from app.api import endpoints

# app = FastAPI()

# app.include_router(endpoints.router)

# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app, host="0.0.0.0", port=8000)

from app.retsinformation.splitter import Split

splitter = Split(
    "app/retsinformation/data/lejeloven.pdf",
    "app/retsinformation/data/lejeloven.md",
    "app/retsinformation/data/lejeloven_chunks.json",
)
splitter.run()
