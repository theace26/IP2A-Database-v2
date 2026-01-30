# 4. S3 Storage Setup (Backblaze B2)

**Duration:** 30-45 minutes
**Goal:** Configure cloud storage for document uploads

Backblaze B2 is recommended because:
- S3-compatible API (works with existing code)
- 10 GB free storage
- 1 GB/day free downloads
- Much cheaper than AWS S3

---

## Option A: Backblaze B2 (Recommended)

### Step 1: Create Backblaze Account

1. Go to https://www.backblaze.com/b2
2. Click **"Sign Up Free"**
3. Verify your email

### Step 2: Create a Bucket

1. In B2 Cloud Storage dashboard, click **"Create a Bucket"**
2. Configure:
   - Bucket Name: `ip2a-documents-prod` (must be globally unique)
   - Files in Bucket: **Private**
   - Default Encryption: **Enable**
   - Object Lock: **Disable**
3. Click **"Create Bucket"**
4. Note the **Bucket Name** and **Endpoint**:
   - Endpoint format: `s3.us-west-002.backblazeb2.com`

### Step 3: Create Application Key

1. Go to **"App Keys"** in sidebar
2. Click **"Add a New Application Key"**
3. Configure:
   - Name: `ip2a-api-key`
   - Allow Access to Bucket: Select `ip2a-documents-prod`
   - Type of Access: **Read and Write**
4. Click **"Create New Key"**
5. **IMPORTANT: Copy these immediately** (shown only once):
   - keyID → `S3_ACCESS_KEY_ID`
   - applicationKey → `S3_SECRET_ACCESS_KEY`

### Step 4: Note Your Credentials

```bash
S3_ENDPOINT_URL=https://s3.us-east-005.backblazeb2.com
S3_ACCESS_KEY_ID=your-key-id-here
S3_SECRET_ACCESS_KEY=your-secret-key-here
S3_BUCKET_NAME=ip2a-documents-prod
S3_REGION=us-east-005
```

Region is in your endpoint URL (e.g., `us-east-005`).

---

## Option B: AWS S3

If you prefer AWS:

### Step 1: Create S3 Bucket

1. Go to AWS S3 Console
2. Click **"Create bucket"**
3. Configure:
   - Name: `ip2a-documents-prod`
   - Region: `us-west-2` (or nearest)
   - Block all public access: **Yes**
   - Versioning: Optional (recommended)
4. Click **"Create bucket"**

### Step 2: Create IAM User

1. Go to IAM Console
2. Click **"Users"** → **"Add users"**
3. Configure:
   - Name: `ip2a-s3-user`
   - Access type: **Programmatic access**
4. Attach policy: Create custom policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::ip2a-documents-prod",
                "arn:aws:s3:::ip2a-documents-prod/*"
            ]
        }
    ]
}
```

5. Complete user creation
6. **Copy Access Key ID and Secret Access Key**

### Step 3: Note Your Credentials

```bash
S3_ENDPOINT_URL=https://s3.us-west-2.amazonaws.com
S3_ACCESS_KEY_ID=AKIAxxxxxxxxxxxx
S3_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
S3_BUCKET_NAME=ip2a-documents-prod
S3_REGION=us-west-2
```

---

## Step 5: Update Your Deployments

Add S3 credentials to your deployment platforms:

### Railway

1. Go to your project → web service
2. Click **"Variables"**
3. Add:
   | Variable | Value |
   |----------|-------|
   | `S3_ENDPOINT_URL` | `https://s3.us-west-002.backblazeb2.com` |
   | `S3_ACCESS_KEY_ID` | (your key ID) |
   | `S3_SECRET_ACCESS_KEY` | (your secret key) |
   | `S3_BUCKET_NAME` | `ip2a-documents-prod` |
   | `S3_REGION` | `us-west-002` |

### Render

1. Go to your web service → **"Environment"**
2. Add the same variables
3. Click **"Save Changes"**

---

## Step 6: Verify S3 Connection

After deployment redeploys with new variables:

### Test via API

```bash
# Upload a test file (if you have an upload endpoint)
curl -X POST https://YOUR-APP/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf" \
  -F "entity_type=member" \
  -F "entity_id=1"
```

### Test via Frontend

1. Log in to your deployed app
2. Navigate to **Documents** → **Upload**
3. Upload a test file
4. Verify it appears in the file list

### Test via Shell (Railway/Render)

```python
python -c "
import boto3
from src.config.settings import settings

s3 = boto3.client(
    's3',
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key_id,
    aws_secret_access_key=settings.s3_secret_access_key,
    region_name=settings.s3_region
)

# List buckets
response = s3.list_buckets()
print('Buckets:', [b['Name'] for b in response['Buckets']])

# Upload test
s3.put_object(
    Bucket=settings.s3_bucket_name,
    Key='test/connection-test.txt',
    Body='S3 connection successful!'
)
print('Test file uploaded!')

# Verify
response = s3.get_object(
    Bucket=settings.s3_bucket_name,
    Key='test/connection-test.txt'
)
print('Content:', response['Body'].read().decode())

# Cleanup
s3.delete_object(
    Bucket=settings.s3_bucket_name,
    Key='test/connection-test.txt'
)
print('Test file deleted!')
"
```

---

## CORS Configuration (If Needed)

If uploads fail from browser, configure CORS on your bucket:

### Backblaze B2

1. Go to bucket settings
2. Under **"Bucket Info"**, add CORS rules:

```json
[
    {
        "corsRuleName": "ip2a-cors",
        "allowedOrigins": [
            "https://ip2a-api.onrender.com",
            "https://your-app.up.railway.app"
        ],
        "allowedOperations": [
            "s3_get",
            "s3_put",
            "s3_delete"
        ],
        "allowedHeaders": ["*"],
        "exposeHeaders": ["ETag"],
        "maxAgeSeconds": 3600
    }
]
```

### AWS S3

In bucket settings → Permissions → CORS:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": [
            "https://ip2a-api.onrender.com",
            "https://your-app.up.railway.app"
        ],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3600
    }
]
```

---

## Storage Paths

Your document service organizes files like:

```
ip2a-documents-prod/
├── uploads/
│   ├── members/
│   │   └── john_doe_123/
│   │       └── 2026/01/
│   │           └── resume.pdf
│   ├── students/
│   │   └── jane_smith_456/
│   │       └── 2026/01/
│   │           └── certificate.pdf
│   ├── grievances/
│   │   └── grievance_789/
│   │       └── 2026/01/
│   │           └── complaint.pdf
│   └── salting/
│       └── activity_101/
│           └── 2026/01/
│               └── notes.pdf
```

---

## Cost Estimate

### Backblaze B2 (Recommended)

| Resource | Free Tier | Cost |
|----------|-----------|------|
| Storage | 10 GB | $0.006/GB/mo after |
| Downloads | 1 GB/day | $0.01/GB after |
| Uploads | Unlimited | Free |
| **Demo Usage** | Free | Free |

### AWS S3

| Resource | Free Tier | Cost |
|----------|-----------|------|
| Storage | 5 GB (12 mo) | $0.023/GB/mo |
| Downloads | 100 GB/mo | $0.09/GB |
| Uploads | 2000 PUTs | $0.005/1000 |
| **Demo Usage** | ~Free | ~$1-5/mo |

---

## Security Best Practices

1. **Never commit credentials** - Use environment variables
2. **Use application-specific keys** - Don't use master key
3. **Restrict bucket access** - Only allow what's needed
4. **Enable versioning** - Protect against accidental deletion
5. **Set lifecycle rules** - Auto-delete old versions after 30 days

---

## Troubleshooting

### "Access Denied" Error
- Check key permissions include bucket access
- Verify bucket name matches exactly
- Check region matches endpoint

### "Bucket Not Found" Error
- Bucket names are globally unique
- Verify bucket was created successfully
- Check for typos in bucket name

### Upload Fails Silently
- Check CORS configuration
- Verify file size limits
- Check network/firewall

### Presigned URLs Don't Work
- Verify endpoint URL is correct
- Check key has GetObject permission
- Ensure bucket is private (public doesn't need presigned)

---

**S3 storage configured!** ✅

**Next:** `5-VERIFICATION.md` →
