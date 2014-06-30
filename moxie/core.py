import os

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://moxie:moxie@localhost:5432/moxie'
)
