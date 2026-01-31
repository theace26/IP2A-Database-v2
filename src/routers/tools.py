from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.db.session import get_db
from src.schemas.tools import (
    ToolIssuedCreate,
    ToolIssuedUpdate,
    ToolIssuedRead,
)
from src.services import tools_service

router = APIRouter(prefix="/tools", tags=["Tools Issued"])


@router.post("/", response_model=ToolIssuedRead)
def create_tool(data: ToolIssuedCreate, db: Session = Depends(get_db)):
    return tools_service.create_tool(db, data)


@router.get("/", response_model=List[ToolIssuedRead])
def list_tools(db: Session = Depends(get_db)):
    return tools_service.list_tools(db)


@router.get("/{tool_id}", response_model=ToolIssuedRead)
def get_tool(tool_id: int, db: Session = Depends(get_db)):
    tool = tools_service.get_tool(db, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.patch("/{tool_id}", response_model=ToolIssuedRead)
def update_tool(tool_id: int, data: ToolIssuedUpdate, db: Session = Depends(get_db)):
    tool = tools_service.update_tool(db, tool_id, data)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.delete("/{tool_id}")
def delete_tool(tool_id: int, db: Session = Depends(get_db)):
    success = tools_service.delete_tool(db, tool_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"message": "Tool deleted successfully"}


@router.get("/student/{student_id}", response_model=List[ToolIssuedRead])
def list_tools_by_student(student_id: int, db: Session = Depends(get_db)):
    return tools_service.list_tools_by_student(db, student_id)
