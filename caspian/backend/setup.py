from setuptools import setup, find_packages

setup(
    name="caspian",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
        "sqlalchemy[asyncio]",
        "asyncpg",
        "passlib[bcrypt]",
        "python-jose[cryptography]",
        "discord.py",
        "httpx",
        "pydantic",
    ],
)
