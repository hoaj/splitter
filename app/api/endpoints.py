from fastapi import APIRouter
from app.retsinformation_splitter.splitter import function1

router = APIRouter()


@router.get("/")
def endpoint1():
    return function1()
