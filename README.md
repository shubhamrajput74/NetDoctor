# NetDoctor

**Layer-Aware Network Troubleshooting & Performance Analysis System**

NetDoctor is a Python and Streamlit application that runs practical network checks and presents results mapped to the seven OSI layers. It includes connectivity diagnostics, performance measurements, recommendations, diagnostic exports, and run history.

> **Important:** NetDoctor is a diagnostic aid, not a guarantee that every network service is healthy. When deployed to Streamlit Community Cloud, checks run from the cloud server—not from the visitor's laptop or Wi-Fi network. Some checks, especially gateway discovery, ARP, and ICMP ping, may be unavailable or restricted in cloud environments.

## Features

- Network interface and IP information
- Default gateway discovery and gateway ARP checks where supported
- Ping latency, packet loss, and jitter where supported
- TCP connection timing
- TLS session setup, negotiated TLS information, and certificate validity
- DNS lookup and HTTPS request timing
- OSI-layer health summary and evidence-based recommendations
- Diagnostic report and performance-history CSV exports
- Simulated diagnostic scenarios for testing diagnosis and recommendation logic

## Project structure

```text
NetDoctor/
├── app.py
├── checks.py
├── requirements.txt
├── test_diagnostics.py
├── .gitignore
└── README.md
```

The `.venv/` directory is created locally and should not be committed to Git.

## Requirements

- Python 3.10 or later (use a version supported by the installed dependencies and hosting platform)
- Git
- Internet access for the external DNS, TCP, TLS, and HTTPS checks

## Run NetDoctor on your own computer

### 1. Clone the repository

Replace the URL below if the repository address changes:

```bash
git clone https://github.com/shubhamrajput74/NetDoctor.git
cd NetDoctor
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the dashboard

```bash
python -m streamlit run app.py
```

Open the local URL printed in the terminal, usually:

```text
http://localhost:8501
```

Click **Run Full Diagnosis** to run the checks. The Performance History tab can compare runs within the current Streamlit session; history may reset when the session restarts.

## Run the simulated diagnostic tests

The test script feeds synthetic results into the diagnosis and recommendation logic. It does not intentionally change network settings or test real connectivity.

```powershell
python test_diagnostics.py
```

The scenarios cover a healthy connection, high jitter, gateway ping warnings, and certificate validity problems.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/).
3. Create an app and select this repository.
4. Choose the `main` branch and set the main file path to `app.py`.
5. Deploy the app and use the generated `streamlit.app` URL.

See the [official Streamlit deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

### Cloud deployment limitation

A hosted Streamlit app executes Python on the cloud server. Therefore, it generally cannot inspect a visitor's private Wi-Fi adapter, local gateway, or ARP table. The online version diagnoses the network environment available to the server. For diagnostics of a visitor's own device, a separate local agent or desktop application would be needed.

## Updating the GitHub repository

After editing files locally:

```powershell
git add README.md app.py checks.py requirements.txt
git commit -m "Update NetDoctor documentation and code"
git push
```

Streamlit Community Cloud normally redeploys after changes are pushed to the configured branch.

## Privacy and safety

- Do not commit passwords, API keys, access tokens, or `.env` files.
- The app performs network requests to its configured test destinations (currently including `1.1.1.1` and `example.com`).
- Diagnostic results are point-in-time observations and may be affected by firewalls, VPNs, DNS caching, ICMP filtering, and destination availability.
- Only run the application on systems and networks you are authorized to test.

## Author

**Shubham Rajput**  
Registration No.: 24BCE0869

NetDoctor is an academic Computer Networks project.
