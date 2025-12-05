from sqlalchemy.orm import Session
from app.models.tools_issued import ToolsIssued
from app.schemas.tools import ToolIssuedCreate, ToolIssuedUpdate


# ------------------------------------------------------------
# GET
# ------------------------------------------------------------
def get_tool(db: Session, tool_id: int) -> ToolsIssued | None:
    return db.query(ToolsIssued).filter(ToolsIssued.id == tool_id).first()

def list_tools(db: Session):
    return db.query(ToolsIssued).all()

def list_tools_by_student(db: Session, student_id: int):
    return db.query(ToolsIssued).filter(ToolsIssued.student_id == student_id).all()

# ------------------------------------------------------------
# CREATE
# ------------------------------------------------------------
def create_tool(db: Session, data: ToolIssuedCreate) -> ToolsIssued:
    obj = ToolsIssued(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------
def update_tool(db: Session, tool_id: int, data: ToolIssuedUpdate):

    obj = get_tool(db, tool_id)
    if not obj:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)

    db.commit()
    db.refresh(obj)
    return obj

# ------------------------------------------------------------
# DELETE
# ------------------------------------------------------------
def delete_tool(db: Session, tool_id: int) -> bool:
    obj = get_tool(db, tool_id)
    if not obj:
        return False

    db.delete(obj)
    db.commit()
    return True
