use std::io::{Read, Write};
use std::fs::File;
use serde::Deserialize;
use csv::Reader;
use sqlite::Connection;
use clap::{arg, Parser};

mod graph;
mod storage;

use graph::*;
use storage::*;

/// Represents the command line arguments that can be used with this software.
#[derive(clap::Parser, Debug, Clone)]
struct CommandArguments {
    #[arg(help="The location of the database")]
    db_path: String,
    #[arg(help="The create tables script")]
    create_path: String,
    #[arg(help="The output path")]
    output: String,
    #[arg(short, long, default_value_t = false)]
    distances: bool
}

/// Opens the CSV files for importing.
fn open_files() -> Result<(File, File, File), std::io::Error> {
    let paths = ("./import/nodes.csv", "./import/edges.csv", "./import/tags.csv");

    Ok( (File::open(paths.0)?, File::open(paths.1)?, File::open(paths.2)?) )
}

/// Extracts all contents of a `File` into a list of `T`.
fn csv_extract<T>(file: File) -> Result<Vec<T>, std::io::Error> where T: for<'a> Deserialize<'a> {
    let mut reader = Reader::from_reader(file);
    let mut nodes: Vec<T> = vec![];

    for result in reader.deserialize() {
        let node: T = result?;
        nodes.push(node);
    }

    Ok( nodes )
}

/// Converts the nodes & edges into a graph, and then computes all the distances. Then, stores these distances as JSON. 
fn process_nodes(nodes: &[Node], edges: Vec<Edge>, path: String) -> Result<(), std::io::Error> {
    let mut result_file = File::create(path)?;

    let graph = Graph::build(nodes, edges);
    let result_matrix = graph.compute_distances();

    let serialized = serde_json::to_string_pretty(&result_matrix).expect("Unable to serialize");
    println!("Writing distances output to file ({} characters)", serialized.len());
    result_file.write_all(serialized.as_bytes())?;
    Ok(())
}

/// Takes the information from the CSV parsings, and inserts it into the SQLite database.
fn db_insert(nodes: Vec<Node>, tags: Vec<NodeTags>, db_path: String, create_path: String) -> Result<(), sqlite::Error> {
    println!("Opening database at '{}'", &db_path);
    let connection = Connection::open(db_path)?;
    connection.execute("BEGIN TRANSACTION")?;

    println!("Removing old database data");
    connection.execute("DROP TABLE IF EXISTS NODES; DROP TABLE IF EXISTS NODE_TAGS;")?;

    println!("Importing create tables script from '{}'", &create_path);
    {
        let mut create_tables_file = File::open(create_path).expect("unable to open create-tables file");
        let mut create_tables = String::new();
        create_tables_file.read_to_string(&mut create_tables).expect("unable to read from the create tables script.");

        connection.execute(create_tables)?;
    }
    println!("Tables created.");

    println!("Inserting {} node(s)", nodes.len());
    for node in nodes {
        connection.execute(
            format!(
                "INSERT INTO NODES (N_ID, X, Y, NODE_NAME, NODE_GROUP, IS_PATH) VALUES ({}, {}, {}, '{}', '{}', {})", node.n_id, node.x, node.y, node.name, node.group, node.is_path
            )
        )?;
    }

    println!("Inserting {} tag(s)", tags.len());

    for tag in tags {
        connection.execute(
            format!(
                "INSERT INTO NODE_TAGS (N_ID, TAG) VALUES ({}, '{}')", tag.n_id, tag.tag
            )
        )?
    }

    println!("Database insert complete. Commiting changes");
    connection.execute("COMMIT")?;

    Ok(())
}

/// Converts an SQL error into a IO error.
fn map_sql_error(x: sqlite::Error) -> std::io::Error {
    std::io::Error::new(std::io::ErrorKind::InvalidData, x)
}

/// Processes the arguments and runs the program.
fn run(args: CommandArguments) -> Result<(), std::io::Error> {
    println!("Opening source files in './import/*'");
    let (nodes, edges, tags) = open_files()?;

    println!("Extracting information");
    let nodes: Vec<Node> = csv_extract(nodes)?;
    let edges: Vec<Edge> = csv_extract(edges)?;
    let tags: Vec<NodeTags> = csv_extract(tags)?;

    println!("Information extracted. {} nodes, {} edges, {} tags", nodes.len(), edges.len(), tags.len());

    if args.distances {
        println!("Begining distance computing");
        process_nodes(&nodes, edges, args.output)?;

        println!("Distance computing complete.");
    }
    else {
        println!("Distance computing is being skipped.");
    }

    println!("Starting database insert");
    if let Err(e) = db_insert(nodes, tags, args.db_path, args.create_path) {
        eprintln!("Database error '{e}'");
        return Err(map_sql_error(e))
    }

    println!("All tasks are complete.");

    Ok( () )
}

fn main() {
    let arguments = CommandArguments::parse();
    println!("SSEB Shortest Path & Database Utility, Version 0.1.0");

    if let Err(e) = run(arguments) {
        eprintln!("{e}");
    }
}
