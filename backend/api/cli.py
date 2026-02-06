"""CLI utility to create an admin user."""

import argparse
import asyncio

from sqlalchemy import select

from api.core.security import get_password_hash
from vector_db.database import Base, async_session_maker, engine
from vector_db.models.user import User, UserRole


async def create_admin(email: str, password: str, full_name: str | None = None) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()

        if existing:
            existing.role = UserRole.ADMIN
            existing.hashed_password = get_password_hash(password)
            if full_name:
                existing.full_name = full_name
            print(f"Updated existing user '{email}' to admin.")
        else:
            user = User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name=full_name,
                role=UserRole.ADMIN,
            )
            session.add(user)
            print(f"Created admin user '{email}'.")

        await session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--name", default=None, help="Full name")
    args = parser.parse_args()

    asyncio.run(create_admin(args.email, args.password, args.name))


if __name__ == "__main__":
    main()
