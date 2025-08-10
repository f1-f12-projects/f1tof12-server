# F1toF12 Server API

## Setup
```bash
pip install -r requirements.txt
python run.py
```

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - Login and get JWT token

### Protected Routes
- `GET /protected` - Test protected route
- `GET /users` - Get all users (requires authentication)

## Usage
1. Register: `POST /register` with `{"username": "test", "password": "test123"}`
2. Login: `POST /login` with same credentials to get token
3. Use token in Authorization header: `Bearer <token>`