Tranzr — Fault-Tolerant File Transfer Backend

Tranzr is a fault-tolerant backend system designed for reliable large file transfers.
It supports chunked uploads, resumable transfers, integrity verification, and secure shareable download links.

Built to simulate how real-world systems like Google Drive, Dropbox, and WeTransfer handle large file delivery at scale.

🧠 Problem It Solves

Uploading large files over unstable networks often leads to:

❌ Upload failures at 90% completion

❌ Having to restart entire uploads

❌ Corrupted files after transfer

❌ No secure way to share large files

Tranzr fixes this using chunked, resumable, and verifiable uploads.

✨ Core Features
📤 1. Chunked Uploads

Files are split into smaller chunks and uploaded individually.
If the network fails, only missing chunks are retried — not the whole file.

🔄 2. Resume Support

Clients can query the server to know which chunks are already uploaded and resume from there.

🔐 3. Integrity Verification

After merging, the system generates a SHA-256 hash to ensure the file is not corrupted.

🔗 4. Secure Share Links

Users can create:

Password-protected download links

Expiring links

Limited download count links

🧹 5. Automatic Cleanup

Abandoned or incomplete uploads are automatically removed after a time threshold.

🗑 6. Complete File Deletion

Deletes:

File metadata

All chunk records

Share links

Physical storage files

🏗 System Architecture
Client
  │
  ├── Start Upload → Server creates file session
  │
  ├── Upload Chunks → Stored individually
  │
  ├── Resume Check → Server tells missing chunks
  │
  ├── Merge Request → Server merges chunks
  │
  └── Share / Download

🛠 Tech Stack
Layer	Technology
Backend Framework	FastAPI
Database	MySQL
ORM	SQLAlchemy
File Storage	Local Disk
Hashing	SHA-256
Server	Uvicorn
📂 Database Design
files

Stores main file metadata

file_id (UUID)

filename

file_size

chunk_size

total_chunks

status (uploading/completed)

file_hash

chunks

Tracks each uploaded chunk

file_id

chunk_index

uploaded

share_links

Controls secure downloads

share_token

password (hashed)

expires_at

download_count

max_downloads

🔌 API Endpoints
📤 Upload Flow
Step	Method	Endpoint	Description
Start Upload	POST	/upload/start	Creates upload session
Upload Chunk	POST	/upload/chunk	Uploads a single chunk
Check Status	GET	/upload/status/{file_id}	Lists uploaded/missing chunks
Merge File	POST	/upload/merge/{file_id}	Merges chunks into final file
📥 Download
Method	Endpoint	Description
GET	/download/{file_id}	Downloads completed file
🔗 Share System
Method	Endpoint	Description
POST	/share/create/{file_id}	Creates secure share link
GET	/share/download/{token}?password=	Downloads via share link
📁 File Management
Method	Endpoint	Description
GET	/files	Lists all files
DELETE	/files/{file_id}	Deletes file and all associated data
🔄 Upload Workflow Example

1️⃣ Start Upload

POST /upload/start
{
  "filename": "video.mp4",
  "file_size": 33.5,
  "chunk_size": 5
}


2️⃣ Upload Chunks
Each chunk is uploaded with:

file_id

chunk_index

binary chunk file

3️⃣ Resume Support

GET /upload/status/{file_id}


4️⃣ Merge

POST /upload/merge/{file_id}


5️⃣ Download

GET /download/{file_id}

🔐 Share Link Example

Create secure link:

POST /share/create/{file_id}?expire_minutes=60&max_downloads=5


Response:

{
  "share_url": "http://server/share/download/TOKEN",
  "password": "generated_password"
}


Download using:

GET /share/download/TOKEN?password=generated_password

🧪 Edge Cases Handled

✔ Network interruption during upload
✔ Duplicate chunk uploads (idempotent)
✔ Last chunk smaller than chunk size
✔ Expired share links
✔ Download limit exceeded
✔ Missing chunk detection before merge
✔ Automatic cleanup of abandoned uploads

🚀 How to Run
pip install -r requirements.txt
uvicorn backend.main:app --reload


Swagger UI:

http://127.0.0.1:8000/docs

🎯 Why This Project Stands Out

This is not a basic CRUD app.
It demonstrates real backend engineering concepts:

Fault tolerance

Resumable uploads

Data integrity

Secure file distribution

Resource cleanup

Production-style API design

This is the kind of backend logic used in cloud storage systems.

📌 Future Improvements

Cloud storage support (AWS S3 / GCS)

Parallel chunk uploads

WebSocket progress updates

Virus scanning before merge

Rate limiting & auth

👨‍💻 Author

Purnendu Sekhar Singha Roy
Backend Developer | Systems Thinker | Problem Solver
