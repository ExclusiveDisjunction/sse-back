# Server Deployment
The intended deployment destination for this application, is the Google Cloud [Compute Engine](https://console.cloud.google.com). 

In order to host on this platform, an account and ample credits are required. These credits can be purchased [here](https://console.cloud.google.com/billing).

One an account and ample credits are procured, the next step is firewall configuration.

## Firewall Configuration
1. Go to the Google Cloud Console.
    
2. Navigate to `VPC network` > `Firewall rules`.
    
3. Click **"Create firewall rule"**.
	
4. Complete the following:

| Field                   | Value                                                                |
| ----------------------- | -------------------------------------------------------------------- |
| **Name**                | `allow-port-5000`                                                    |
| **Network**             | `default` _(or your network)_                                        |
| **Priority**            | `1000` _(default is fine)_                                           |
| **Direction**           | `Ingress`                                                            |
| **Action on match**     | `Allow`                                                              |
| **Targets**             | `All instances in the network` _(or specify a target tag if needed)_ |
| **Source IP ranges**    | `0.0.0.0/0` _(allow from anywhere)_                                  |
| **Protocols and ports** | `Specified protocols and ports` > check `tcp` and enter `5000`       |
5. Click **Create**. 

## Environment Setup
This application requires several dependancies, all of which can be found in the 'Dependancies.txt' file. 

To install them, begin by creating  a virtual python environment (Conda or Venv).

Create environment
```text
python3 -m venv <environment name here>
```

Activate (Windows)
```text
venv\Scripts\activate.bat
```

Linux 
```text
source venv/bin/activate
```

Install dependancies
```text
pip install -r Dependencies.txt
```

## Local Host Exposure
In order to securely expose the back ender server which is being served on `127.0.0.1:5000`, an NGROK tunneling service is required. 

Follow below to install NGROK:

Linux (Debian)
```text
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \

echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list && \

sudo apt update && sudo apt install ngrok
```

Windows
- Download the ZIP from https://ngrok.com/download
    
- Extract it
    
- Move the executable to a folder in your PATH (e.g., `C:\ngrok\ngrok.exe`)

Sign in and generate token:
1. Go to https://dashboard.ngrok.com/signup
    
2. Sign up and copy your **authtoken**
    
Then run this command once:
```text
ngrok config add-authtoken <your_token_here>
```

## Start Server and Tunneling Service
To start the server, run the following command form the `src` folder.

```text
python3 main.py
```

To engage the tunneling service, run the following command from anywhere in you virtual environment:

```text
ngrok http https://127.0.0.1:5000
```

Now, the server should up and broadcasted through the public NGROK url.