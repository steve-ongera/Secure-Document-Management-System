# Mini HMIS — Secure Document Management Module

A small, focused slice of a Hospital Management Information System:
patients, and the documents (photos, lab reports, X-rays, prescriptions,
discharge summaries, insurance docs) linked to them — uploaded, validated,
stored, and audited securely.

## Models (3)

- **Patient** — minimal identity record documents attach to.
- **Document** — file metadata + path (the binary lives on disk/object
  storage, not in Postgres). Validates file type/size, randomizes the
  stored filename, namespaces storage by patient + document type.
- **DocumentAuditLog** — append-only record of every upload/view/download/
  archive, with user + IP, so access to sensitive files is traceable.

## Backend setup

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# create a .env or export DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/token/` | Obtain JWT access/refresh pair |
| POST | `/api/token/refresh/` | Refresh access token |
| GET/POST | `/api/patients/` | List / create patients |
| GET/PATCH/DELETE | `/api/patients/{id}/` | Retrieve / update / delete a patient |
| GET/POST | `/api/documents/` | List (filter by `?patient=`, `?document_type=`) / upload a document |
| GET/PATCH/DELETE | `/api/documents/{id}/` | Retrieve (logs a "view") / update / delete |
| GET | `/api/documents/{id}/download/` | Stream file (logs a "download") |
| POST | `/api/documents/{id}/archive/` | Soft-delete (logs an "archive") |

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` if the backend isn't on `http://localhost:8000/api`.

## Design decisions worth mentioning in an interview

- **Files off the DB row.** `Document.file` stores a path; the actual
  bytes go to `MEDIA_ROOT` (swap to S3/GCS in production by changing
  `DEFAULT_FILE_STORAGE` only — the model/serializer don't change).
- **Filename is never trusted.** Uploaded files are renamed to a UUID on
  the way in; the original name is kept only as metadata for display/
  download.
- **Validation happens twice.** Once in the serializer (fails fast with
  a clean 400 before touching storage) and again in `Document.clean()`
  as a model-level backstop for anything that bypasses the API (admin,
  management commands, scripts).
- **Every read and write is audited.** `DocumentAuditLog` entries are
  created on upload, view, download, and archive — not just delete —
  because "who looked at this insurance document" is as important as
  "who uploaded it."
- **Soft delete only.** `archive()` flips a flag instead of calling
  `.delete()`, preserving both the file and its audit trail for
  compliance.