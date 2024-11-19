import os
from sqlalchemy import Float, select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from dotenv import load_dotenv
from sqlalchemy import (
    DateTime,
    String,
    func,
    Integer,
    Boolean,
    BigInteger,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


#from .env file:
# DB_LITE=sqlite+aiosqlite:///my_base.db
# DB_URL=postgresql+asyncpg://login:password@localhost:5432/db_name

# engine = create_async_engine(os.getenv('DB_LITE'), echo=True)

load_dotenv()

engine = create_async_engine(os.getenv('DB_URL'))

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        
        


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class Rate(Base):
    __tablename__ = "rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    currency: Mapped[str] = mapped_column(String(255), nullable=False)
    rate: Mapped[float] = mapped_column(Float, nullable=False)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ---------- ADD RATE ----------
async def orm_add_rate(currency: str, rate: float):
    async with session_maker() as session:
        async with session.begin():
            try:
                obj = Rate(currency=currency, rate=rate)
                session.add(obj)
                await session.commit()
                return obj
            except Exception as e:
                print(e)
                return None

# ---------- GET RATE ----------
async def orm_get_rate(rate_id: int):
    async with session_maker() as session:
        async with session.begin():
            try:
                query = select(Rate).where(Rate.id == rate_id)
                result = await session.execute(query)
                return result.scalar()
            except Exception as e:
                print(e)
                return None

# ---------- GET ALL RATES ----------
async def orm_get_rates():
    async with session_maker() as session:
        async with session.begin():
            try:
                query = select(Rate)
                result = await session.execute(query)
                return result.scalars().all()
            except Exception as e:
                print(e)
                return None

# ---------- REMOVE RATE ----------
async def orm_remove_rate(rate_id: int):
    async with session_maker() as session:
        async with session.begin():
            try:
                query = delete(Rate).where(Rate.id == rate_id)
                await session.execute(query)
                await session.commit()
                return True
            except Exception as e:
                print(e)
                return None

# ---------- UPDATE RATE ----------
async def orm_update_rate(rate_id: int, rate: float):
    async with session_maker() as session:
        async with session.begin():
            try:
                query = update(Rate).where(Rate.id == rate_id).values(rate=rate)
                await session.execute(query)
                await session.commit()
                return True
            except Exception as e:
                print(e)
                return None

# ---------- ADD USER BY ID ----------
async def orm_add_user(tg_id: int, name: str = None):
    async with session_maker() as session:
        async with session.begin():
            try:
                obj = User(tg_id=tg_id, name=name)
                session.add(obj)
                await session.commit()
                return obj
            except Exception as e:
                print(e)
                return None


# ---------- ADD USER BY NAME ----------
async def orm_add_user_by_name(name: str):
    async with session_maker() as session:
        async with session.begin():
            try:
                obj = User(name=name)
                session.add(obj)
                await session.commit()
                return obj
            except Exception as e:
                print(e)
                return None


# ---------- REMOVE USER ----------
async def orm_remove_user(name: str):
    async with session_maker() as session:
        async with session.begin():
            try:
                query = delete(User).where(User.name == name)
                await session.execute(query)
                await session.commit()
            except Exception as e:
                print(e)
                return None


# ---------- GET USER ----------
async def orm_get_user(tg_id: int):
    async with session_maker() as session:
        async with session.begin():
            try:
                query = select(User).where(User.tg_id == tg_id)
                result = await session.execute(query)
                return result.scalar()
            except Exception as e:
                print(e)
                return None


# ---------- GET USERS ----------
async def orm_get_users():
    async with session_maker() as session:
        async with session.begin():
            try:
                query = select(User)
                result = await session.execute(query)
                return result.scalars().all()
            except Exception as e:
                print(e)
                return None


# ---------- IS ADMIN ----------
async def orm_is_admin(tg_id: int):
    async with session_maker() as session:
        async with session.begin():
            try:
                query = select(User).where(User.tg_id == tg_id)
                result = await session.execute(query)
                user = result.scalar()
                
                if user:
                    return user.is_admin
                else:
                    await orm_add_user(tg_id)
                    return False
            except:
                return None

# ---------- ADD CHANNEL ---------- 
async def orm_add_channel(channel_id: str):
    async with session_maker() as session:
        async with session.begin():
            try:
                obj = Channel(channel_id=channel_id)
                session.add(obj)
                await session.commit()
                return obj
            except Exception as e:
                print(e)
                return None

# ---------- REMOVE CHANNEL ---------- 
async def orm_remove_channel(channel_id: str):
    async with session_maker() as session:
        async with session.begin():
            try:
                query = delete(Channel).where(Channel.channel_id == channel_id)
                await session.execute(query)
                await session.commit()
                return True
            except Exception as e:
                print(e)
                return None

# ---------- GET ALL CHANNELS ---------- 
async def orm_get_channels():
    async with session_maker() as session:
        async with session.begin():
            try:
                query = select(Channel)
                result = await session.execute(query)
                return result.scalars().all()
            except Exception as e:
                print(e)
                return None
