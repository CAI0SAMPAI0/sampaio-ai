from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.config import settings
from core.database import create_tables
from routers import auth, conversations, messages


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title='Sampaio AI',
    description='An AI assistant for developers.',
    version='1.0.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.get('/')
async def health_check():
    return {'message': 'Sampaio AI is running!'}


# adicionando rotas

app.include_router(auth.router,          prefix="/api/auth",          tags=["auth"])
app.include_router(conversations.router, prefix="/api/conversations",  tags=["conversations"])
app.include_router(messages.router,      prefix="/api/conversations",  tags=["messages"])