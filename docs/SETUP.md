# dv2png Setup Guide

## Overview

dv2png is a web-based FISH image converter for the O'Nishimura lab. It provides a user-friendly interface to process `.dv` microscopy images, extract channels, create composite images, and generate PDF reports.

The app supports:
- **Local execution** — Process images on your local machine
- **Alpine HPC submission** — Submit jobs to CU Boulder's Alpine cluster

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend)
- pip or conda

### 1. Clone and Setup Backend

```bash
cd dv2png/backend

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure NAS Access

```bash
# Copy config template
cp config.example.yaml config.yaml

# Edit with your lab's NAS details
nano config.yaml
# (Set nas_host, nas_user, nas_password, nas_share)
```

### 3. Run Backend Server

```bash
python app.py
```

Server will start on `http://localhost:5000`

### 4. Setup and Run Frontend

```bash
cd dv2png/frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend will open at `http://localhost:3000`

---

## Configuration

### Backend Configuration (backend/config.yaml)

```yaml
nas:
  nas_host: "your_nas_hostname"
  nas_user: "your_username"
  nas_password: "your_password"
  nas_share: "share_name"

channels:
  0: "Cy5"
  1: "mCherry"
  2: "FITC"
  3: "DAPI"

processing:
  scale_factor: 2.0
  brightness_factor: 2
```

**IMPORTANT:** Never commit `config.yaml` to Git. Use `config.example.yaml` as a template.

### Environment Variables (.env)

```bash
FLASK_ENV=development
FLASK_DEBUG=False
PORT=5000
JOBS_DIR=./jobs
CONFIG_FILE=./config.yaml
REACT_APP_API_URL=http://localhost:5000/api
```

---

## API Endpoints

### Health Check
- **GET** `/api/health` — Check if API is running

### Configuration
- **GET** `/api/config` — Get default channels and processing parameters

### Job Management
- **POST** `/api/jobs` — Submit a new processing job
  ```json
  {
    "your_name": "John Doe",
    "imaged_by": "Jane Smith",
    "input_directory": "/path/to/images",
    "output_directory": "/path/to/output",
    "channel_names": {"0": "Cy5", "1": "mCherry", "2": "FITC", "3": "DAPI"},
    "include_channels": ["Cy5", "mCherry", "FITC"],
    "scale_factor": 2.0,
    "brightness_factor": 2,
    "execution_mode": "local"
  }
  ```

- **GET** `/api/jobs` — List all jobs (supports `?limit=50&status=completed`)
- **GET** `/api/jobs/<job_id>` — Get job status and metadata
- **DELETE** `/api/jobs/<job_id>` — Cancel a job

### Results
- **GET** `/api/jobs/<job_id>/results` — List result files
- **GET** `/api/jobs/<job_id>/download/<file_path>` — Download a result file

---

## Deployment

### Local Production

Run with production WSGI server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Alpine HPC

#### Option 1: Use Web UI to Generate SLURM Script

1. Fill out the form in the web UI
2. Select "Alpine HPC" as execution mode
3. Review the generated SLURM script
4. Submit (script will be saved and you can run it manually)

#### Option 2: Manual SLURM Submission

```bash
# Create SLURM script
cat > submit_job.sh << 'EOF'
#!/bin/bash
#SBATCH --job-name=dv2png
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=logs/dv2png_%j.log

module load anaconda
conda activate dv2png

# Copy data from NAS (or assume it's mounted)
# cp -r /path/to/nas/data /scratch/user@colorado.edu/

python processor_runner.py \
  --input /path/to/input \
  --output /path/to/output \
  --your-name "Your Name" \
  --imaged-by "Imager Name" \
  --include-channels "Cy5,mCherry,FITC"

EOF

chmod +x submit_job.sh
sbatch submit_job.sh
```

#### Setup on Alpine

```bash
# SSH into Alpine
ssh user@colorado.edu@login.alpine.colorado.edu

# Clone repo
git clone https://github.com/yourusername/dv2png.git
cd dv2png

# Create conda environment
conda create -n dv2png python=3.10
conda activate dv2png

# Install dependencies
pip install -r backend/requirements.txt

# Copy config template
cp backend/config.example.yaml backend/config.yaml
nano backend/config.yaml  # Fill in NAS credentials
```

---

## Docker Deployment (Optional)

```bash
# Build image
docker build -t dv2png:latest .

# Run container
docker run -p 5000:3000 \
  -v $(pwd)/jobs:/app/jobs \
  -v $(pwd)/config.yaml:/app/backend/config.yaml \
  dv2png:latest
```

---

## File Structure

```
dv2png/
├── backend/
│   ├── app.py              # Flask API server
│   ├── processor.py        # Core image processing logic
│   ├── config.py           # Configuration management
│   ├── models.py           # Data models (JobMetadata, etc.)
│   ├── job_manager.py      # Job storage and retrieval
│   ├── config.yaml         # ⚠️ NEVER COMMIT (has credentials)
│   ├── config.example.yaml # Template for config.yaml
│   └── requirements.txt    # Python dependencies
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── JobForm.jsx       # Parameter input form
│   │   │   └── JobDashboard.jsx  # Job status dashboard
│   │   ├── services/
│   │   │   └── api.js            # API client
│   │   ├── App.jsx
│   │   └── index.jsx
│   └── package.json
│
├── scripts/
│   ├── slurm_generator.py  # SLURM script generation
│   └── local_runner.py     # Standalone runner for Alpine
│
├── docs/
│   └── SETUP.md            # This file
│
├── .env.example            # Environment variable template
├── .gitignore              # Git exclusions
├── .dockerignore
├── Dockerfile
└── README.md
```

---

## Troubleshooting

### NAS Connection Issues

```bash
# Test NAS connection
python -c "
from smb.SMBConnection import SMBConnection
conn = SMBConnection('user', 'pass', 'client', 'nas_host')
conn.connect('nas_host', 445)
print('Connected!')
"
```

### API Not Starting

- Check `requirements.txt` — ensure Flask and flask-cors are installed
- Verify port 5000 is not in use: `lsof -i :5000`
- Check logs in `JOBS_DIR`

### Frontend Build Issues

- Delete `node_modules` and `package-lock.json`, then `npm install`
- Ensure `.env` has correct `REACT_APP_API_URL`

### Job Fails on Alpine

- Check SLURM logs: `cat logs/dv2png_*.log`
- Verify modules loaded: `module list`
- Test conda env: `conda list` (bigfish, numpy, etc.)
- Check input/output paths are accessible

---

## Development Notes

### Adding New Features

1. **Backend changes** → Modify `processor.py` or add new API endpoints in `app.py`
2. **Frontend changes** → Update React components in `frontend/src/`
3. **Configuration** → Add to `config.py` or `models.py`

### Testing Locally

```bash
# Test backend
python -m pytest backend/tests/

# Test frontend
npm test
```

### Security Best Practices

- ✅ Use `.env` for sensitive variables
- ✅ Add authentication layer if deployed on shared network
- ✅ Store credentials in `.gitignore` files only
- ✅ Use HTTPS in production
- ✅ Validate all user inputs

---

## Support & Contributions

For issues or feature requests, contact the lab or open a GitHub issue.

---

**Last Updated:** June 2026
