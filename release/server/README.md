# Server Release Directory

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