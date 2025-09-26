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

## Error codes
1. Success - 200
2. Updated - 
3. Can't insert duplicate record - 409
4. Invalid Input - XXX_400
5. Record Not found - XXX_404
6. Permission issue - 403
7. Type mismatch - 400 - This is similar to Bad request
8. Server Error - 500

### Entities and their codes (XXX):
    Compnay     - COMP
    SPOC        - SPOC
    Recuiter    - RCTR
    Requirement - REQ
    User        - USER
    Invoice     - INV
