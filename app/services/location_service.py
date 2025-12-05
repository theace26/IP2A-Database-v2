from sqlalchemy.orm import Session
from typing import List, Optional

from app.models import Location
from app.schemas.location import LocationCreate, LocationUpdate


# ------------------------------------------------------------
# CREATE
# ------------------------------------------------------------
def create_location(db: Session, data: LocationCreate) -> Location:
    location = Location(
        name=data.name,
        address=data.address,
        city=data.city,
        state=data.state,
        zip_code=data.zip_code,
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


# ------------------------------------------------------------
# READ (Single)
# ------------------------------------------------------------
def get_location(db: Session, location_id: int) -> Optional[Location]:
    return db.query(Location).filter(Location.id == location_id).first()


# ------------------------------------------------------------
# READ (List)
# ------------------------------------------------------------
def list_locations(db: Session, skip: int = 0, limit: int = 100) -> List[Location]:
    return (
        db.query(Location)
        .order_by(Location.name.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------
def update_location(
    db: Session,
    location_id: int,
    data: LocationUpdate
) -> Optional[Location]:

    location = get_location(db, location_id)
    if not location:
        return None

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(location, key, value)

    db.commit()
    db.refresh(location)
    return location


# ------------------------------------------------------------
# DELETE
# ------------------------------------------------------------
def delete_location(db: Session, location_id: int) -> bool:
    location = get_location(db, location_id)
    if not location:
        return False

    db.delete(location)
    db.commit()
    return True
