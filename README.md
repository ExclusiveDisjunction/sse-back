# Secure Software Engineering Project - Back End

This contains all the needed files to run the program. Please be aware of the following dependencies:

1. bcrypt
2. PyJWT
3. flask
4. flask_cors
5. numpy

These should be included in the python standard library, but are mentioned just in case:
1. sqlite3
2. json

This program was developed with Python version 3.13.2.

## File Analysis
1. `main.py`: This is the main entry point, and includes the API bindings & control logic.
2. `db.py`: Contains utilities to load the Sqlite database from the `data.sqlite` file.
3. `graph.py`: Includes graph based logic for path finding.
4. `nodes.py`: Includes utilities for loading and saving information from the database, specifically for nodes.
5. `usr.py`: Includes utilities for loading and saving information from the database, specifically for users.
6. `data.sqlite`: A database contaning the nodes, node tags, and any users that are saved with the program. The program will not run without this file.
7. `dijkstra.json`: A file that contains the precomputed shortests path table. The program will not run without this file.
8. `table_create.sql`: A file used to validate the database. This is required.

Note that `data.sqlite`, and `dijkstra.json` can be re-made, using the `graph` utility included with this software bundle. Please see its documentation for more information.

## To Run
To run this program, ensure that your current working directory is the same as the script's location. 
Then, invoke this command:

```bash
python3 main.py
````

Or, on Windows:
```
python main.py
```

This will boot up the software, and it will report where it is hosting. Please use the front end software to communicate with this software.

## Server Deployment
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