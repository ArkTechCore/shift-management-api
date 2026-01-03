from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.models.store import Store
from app.models.membership import StoreMembership
from app.core.security import get_password_hash
import uuid


def run_seed():
    db: Session = SessionLocal()

    try:
        # ---------- ADMIN USER ----------
        admin_email = "admin@shift.local"

        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                id=uuid.uuid4(),
                email=admin_email,
                hashed_password=get_password_hash("admin123"),
                role="ADMIN",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print("✅ Admin user created")
        else:
            print("ℹ️ Admin user already exists")

        # ---------- DEFAULT STORE ----------
        store_code = "STORE001"

        store = db.query(Store).filter(Store.code == store_code).first()
        if not store:
            store = Store(
                id=uuid.uuid4(),
                name="Main Store",
                code=store_code,
                is_active=True,
            )
            db.add(store)
            db.commit()
            db.refresh(store)
            print("✅ Store created")
        else:
            print("ℹ️ Store already exists")

        # ---------- MEMBERSHIP ----------
        membership = (
            db.query(StoreMembership)
            .filter(
                StoreMembership.user_id == admin.id,
                StoreMembership.store_id == store.id,
            )
            .first()
        )

        if not membership:
            membership = StoreMembership(
                id=uuid.uuid4(),
                user_id=admin.id,
                store_id=store.id,
                store_role="ADMIN",
                pay_rate="0",
            )
            db.add(membership)
            db.commit()
            print("✅ Admin linked to store")
        else:
            print("ℹ️ Admin already linked to store")

    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
