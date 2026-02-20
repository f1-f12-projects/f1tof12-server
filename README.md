# F1toF12 Server API

## Setup
```bash
pip install -r requirements.txt
python run.py
```

## Deployment

### Automated Deployment via GitHub Actions

The application automatically deploys to AWS Lambda when code is pushed to specific branches:

- **Dev Environment**: Push to `dev` branch → Deploys to Dev Lambda
- **Production Environment**: Push to `main` branch → Deploys to Prod Lambda

### How It Works

1. **Code Push**: Developer pushes code to `dev` or `main` branch
2. **GitHub Actions Trigger**: Workflow automatically starts
3. **Package**: Installs dependencies and creates deployment zip
4. **Upload to S3**: Uploads zip file to respective S3 bucket
5. **Update Lambda**: Updates Lambda function with new code from S3
6. **Live**: Changes are immediately live

### Setup Instructions

#### 1. AWS IAM User Setup
Create/use IAM user `f1tof12-github-deployment` with policies:
- `AmazonS3FullAccess`
- `AWSLambda_FullAccess` (or custom policy with `lambda:UpdateFunctionCode`)
- `AmazonSSMReadOnlyAccess`
- `CloudFrontFullAccess`

Generate access keys for this user.

#### 2. GitHub Repository Secrets
Go to Repository Settings → Secrets and variables → Actions → New repository secret:
- `AWS_ACCESS_KEY_ID`: IAM user access key
- `AWS_SECRET_ACCESS_KEY`: IAM user secret key
- `AWS_REGION`: AWS region (e.g., `us-east-1`)

#### 3. GitHub Environment Secrets
Create two environments and add secrets:

**Dev Environment** (Settings → Environments → New environment: `dev`):
- `DEV_S3_BUCKET`: Dev S3 bucket name
- `DEV_LAMBDA_FUNCTION`: Dev Lambda function name

**Production Environment** (Settings → Environments → New environment: `production`):
- `PROD_S3_BUCKET`: Production S3 bucket name
- `PROD_LAMBDA_FUNCTION`: Production Lambda function name

#### 4. Deploy
Push code to trigger deployment:
```bash
git add .
git commit -m "Your changes"``
git push origin dev        # Deploys to dev
git push origin main       # Deploys to production
```

### Monitoring Deployments
View deployment status: Repository → Actions tab

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - Login and get JWT token

### User Management
- `GET /users` - Get all users (requires HR or manager role)
- `GET /user/{username}` - Get user details (requires authentication - own details only)
- `PUT /user/{username}/update` - Update user (requires HR or manager role)
- `POST /user/{username}/enable` - Enable user (requires HR or manager role)
- `POST /user/{username}/disable` - Disable user (requires HR or manager role)
- `POST /user/create` - Create new user (requires manager role)
- `POST /user/{username}/reset-password` - Reset user password (requires HR or manager role)

### Protected Routes
- `GET /protected` - Test protected route

### Leave Management
- `POST /leaves/apply` - Apply for leave (requires authentication)
- `GET /leaves/dashboard` - View leave dashboard (requires authentication)
- `GET /leaves/pending` - View pending leaves for approval (requires lead or HR role)
- `GET /leaves/all` - View all leaves in system (requires lead or HR role)
- `PUT /leaves/{leave_id}/approve` - Approve/reject leave (requires lead or HR role)

### Financial Year Management
- `POST /financial-years` - Create financial year (requires HR role)
- `GET /financial-years` - Get all financial years (requires HR role)
- `GET /financial-years/active` - Get active financial year (requires HR role)
- `PUT /financial-years/{year_id}` - Update financial year (requires HR role)
- `POST /financial-years/{year_id}/activate` - Activate financial year (requires HR role)


### Holiday Management
- `POST /holidays` - Create holiday (requires HR role)
- `GET /holidays/year/{financial_year_id}` - Get holidays by year (requires authentication)
- `GET /holidays/optional/{financial_year_id}` - Get optional holidays (requires authentication)
- `POST /holidays/select/{financial_year_id}` - Select 2 optional holidays (requires authentication)
- `GET /holidays/my-holidays/{financial_year_id}` - Get user's holidays (requires authentication)
- `PUT /holidays/{holiday_id}` - Update holiday (requires HR role)
- `DELETE /holidays/{holiday_id}` - Delete holiday (requires HR role)

## Roles
- **Manager**: Full system access
- **HR**: User management and leave management
- **Lead**: Leave approval and recruiter permissions
- **Finance**: Financial operations
- **Recruiter**: Basic operations (default role)

## API Usage
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
    Leave       - LEAVE
    Financial Year - FY
    Holiday     - HOL
