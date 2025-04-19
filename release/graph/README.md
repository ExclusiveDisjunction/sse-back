# Graph Utility

This utility is used to precompute the shortest paths for all nodes, construct the database, and import all data from its sources.

You can use this utility to create information that the server can run. If you want to change the nodes, change the information in the source CSV files, and then run this utility.

## File Structure
1. `table_create.sql`: The script used to create the database tables.
2. `import/*`: The information sources used by the program.
3. `src/*`: The program's source code.

## To Run
Find the executable that works for your platform & chipset. Then, invoke the program by its name. Ensure that the `import` directory is in the same directory as the executable itself. Otherwise, the program will not run. The arguments for the program are:

```bash
graph [-d | --distances] [-h | --help] [DB_PATH] [CREATE_PATH] [OUTPUT]
```

1. `-d`: Instructs the program to compute all distances, and output to the `OUTPUT` path. If this option is missing, it will still require the `OUTPUT` variable.
2. `-h` Print a help menu
3. `DB_PATH`: The location of the database. This is usually the `data.sqlite` file for the backend.
4. `CREATE_PATH`: A path to the create table script. This is usually `table_create.sql`.
5. `OUTPUT`: A path used to dump the computed distances into. 

Note that this program will input all CSV files, transform the information, and then write back into the database & output file.