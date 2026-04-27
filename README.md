# fastapi_backend
A specialized FastAPI backend developed to use Augmentative and Alternative Communication (AAC) for the Estonian language. This project provides the linguistic and synthesis infrastructure required to assist individuals with communication impairments.

## Integrations
* EstNLTK https://github.com/estnltk/estnltk, the primary toolkit for processing Estonian text (morphological analysis, lemmatization, and synthesis).
* TartuNLP TTS API https://api.tartunlp.ai/text-to-speech/v2 to provide high-quality, neural Estonian voices.

# Installation
Create a virtual environment:

    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:

    pip install -r requirements.txt

Populate .env file:
(Postgres DB, "STORAGE_TYPE=LOCAL" is untested)

    DATABASE_URL=
    APP_URL=
    LOG_LEVEL=
    UPLOAD_DIR=uploads
    IMAGE_BACKGROUND_COLOR=#f7f2fa
    JWT_SECRET=

    SMTP_SERVER=
    SMTP_PORT=
    SMTP_USERNAME=
    SMTP_PASSWORD=
    SENDER_EMAIL=

    DEFAULT_PIN=

    STORAGE_TYPE=CLOUDFLARE
    R2_BUCKET_NAME=
    R2_ACCOUNT_ID=
    R2_ACCESS_KEY=
    R2_SECRET_KEY=
    R2_PUBLIC_URL=

Running the App:

Start the development server with hot-reload:

    uvicorn main:app --reload --port 8000

# API Documentation

Once running, access the auto-generated documentation to test endpoints:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc