# Certificate Management System

A full-stack certificate generation and management system with QR code verification.

## Features

- 📄 **Template Management**: Upload and manage certificate templates
- 🎨 **Visual Editor**: Draw rectangles to position text elements
- 🏆 **Certificate Generation**: Generate certificates with custom text
- 📱 **QR Code Verification**: Verify certificates using QR codes
- 👥 **Admin Dashboard**: Manage certificates, templates, and students
- 🔍 **Public Verification**: Public page to verify certificates

## Tech Stack

### Frontend

- React 18
- TypeScript
- Tailwind CSS
- Framer Motion
- Axios

### Backend

- FastAPI
- Python 3.11
- MongoDB
- Pillow (PIL) for image processing
- QRCode library

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- MongoDB

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

## API Endpoints

- `GET /api/templates` - List all templates
- `POST /api/templates/upload` - Upload new template
- `POST /api/certificates/generate` - Generate certificate
- `GET /api/certificates` - List all certificates
- `GET /verify/{certificate_id}` - Verify certificate

## Deployment

### Frontend (Vercel/Netlify)

1. Build the React app: `npm run build`
2. Deploy to Vercel or Netlify

### Backend (Railway/Render)

1. Deploy FastAPI app to Railway or Render
2. Set up MongoDB Atlas for production
3. Update CORS settings for production domain

## Environment Variables

### Backend

```
MONGODB_URL=mongodb://localhost:27017/student_details
```

### Frontend

```
REACT_APP_API_URL=http://localhost:8000
```

## License

MIT License
