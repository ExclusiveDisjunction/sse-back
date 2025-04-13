use std::cmp::Ordering;
use std::hash::Hash;
use std::io::{Read, Write};
use std::{collections::BinaryHeap, fs::File};
use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use csv::Reader;
use sqlite::Connection;
use clap::{arg, Parser};

fn open_files() -> Result<(File, File, File), std::io::Error> {
    let paths = ("./import/nodes.csv", "./import/edges.csv", "./import/tags.csv");

    Ok( (File::open(paths.0)?, File::open(paths.1)?, File::open(paths.2)?) )
}

#[derive(Serialize, Deserialize, Debug, PartialEq, Clone)]
struct CSVNode {
    n_id: usize,
    x: f32,
    y: f32,
    name: String,
    group: String,
    is_path: i8
}
impl CSVNode {
    fn get_graph(&self) -> GraphNode {
        GraphNode{
            x: self.x,
            y: self.y
        }
    }
}
#[derive(Debug, PartialEq, Clone)]
struct GraphNode {
    x: f32,
    y: f32,
}

#[derive(Serialize, Deserialize, Debug, PartialEq, Eq, Clone)]
struct CSVEdge {
    source: usize,
    dest: usize
}

#[derive(Serialize, Deserialize, Debug, PartialEq, Eq, Clone)]
struct NodeTags {
    n_id: usize,
    tag: String
}

fn csv_extract<T>(file: File) -> Result<Vec<T>, std::io::Error> where T: for<'a> Deserialize<'a> {
    let mut reader = Reader::from_reader(file);
    let mut nodes: Vec<T> = vec![];

    for result in reader.deserialize() {
        let node: T = result?;
        nodes.push(node);
    }

    Ok( nodes )
}

fn path_reconstruct(src: usize, dest: usize, pred: HashMap<usize, Option<usize>>) -> Option<Vec<usize>> {
    let mut result = vec![];
    let mut v = dest;
    while v != src {
        result.push(v);
        v = pred.get(&v).copied()??;
    }

    result.push(v);
    result.reverse();

    Some(result)
}

#[derive(PartialEq, Debug, Clone)]
struct DijkstrasEntry {
    id: usize,
    value: f32
}
impl Eq for DijkstrasEntry { }
impl PartialOrd for DijkstrasEntry {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}
impl Ord for DijkstrasEntry {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        if self.value == other.value { return Ordering::Equal }

        // NOte these are flipped because the rust library has a max heap, I need min heap.
        if self.value < other.value {
            Ordering::Greater
        }
        else {
            Ordering::Less
        }
    }
}
#[derive(Serialize, Deserialize, Clone, Debug, Default, PartialEq)]
struct DijkstrasResult {
    points: Vec<usize>,
    dist: f32
}
impl Hash for DijkstrasResult {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.points.hash(state);
        (self.dist as i64).hash(state);
    }
}
impl Eq for DijkstrasResult { }
impl DijkstrasResult {
    fn new(points: Vec<usize>, dist: f32) -> Self {
        Self {
            points,
            dist
        }
    }
}

#[derive(clap::Parser, Debug, Clone)]
struct CommandArguments {
    #[arg(help="The location of the database")]
    db_path: String,
    #[arg(help="The create tables script")]
    create_path: String,
    #[arg(short, long, default_value_t = false)]
    distances: bool
}

fn dijkstras(source: usize, dest: usize, nodes: &HashMap<usize, GraphNode>, adj: &[Vec<Option<f32>>]) -> Option<DijkstrasResult> {
    if source == dest {
        return Some( DijkstrasResult::default() )
    }

    let mut dist: HashMap<usize, f32> = HashMap::new();
    let mut pred: HashMap<usize, Option<usize>> = HashMap::new();
    let mut visited: HashMap<usize, bool> = HashMap::new();
    for node in nodes.iter() {
        dist.insert(*node.0, f32::INFINITY);
        pred.insert(*node.0, None);
        visited.insert(*node.0, false);
    }

    *dist.get_mut(&source).unwrap() = 0.0;

    let mut pq: BinaryHeap<DijkstrasEntry> = BinaryHeap::new();
    pq.push(DijkstrasEntry { id: source, value: 0.0 } );

    while !pq.is_empty() {
        let last = pq.pop().unwrap();
        let u = last.id;

        if u == dest {
            return Some( DijkstrasResult::new(path_reconstruct(source, dest, pred)?, dist.get(&u).cloned()? ) )
        }

        if *visited.get(&u).unwrap() {
            continue;
        }

        let neighbors = &adj[u];
        for (v, weight) in neighbors.iter().enumerate() {
            let weight = match weight {
                Some(val) => *val,
                None => continue
            };
            
            if *visited.get(&v).unwrap() {
                continue;
            }

            let at_u = *dist.get(&u).unwrap();

            if at_u != f32::INFINITY && (at_u + weight) < *dist.get(&v).unwrap() {
                let new_dist = at_u + weight;
                dist.insert(v, new_dist);
                pred.insert(v, Some(u));
                pq.push(DijkstrasEntry { id: v, value: new_dist });
            }
        }
    }

    None
}

type TableEntry = (usize, DijkstrasResult);
type DijkstrasTable = Vec<Vec<Option<TableEntry>>>;

fn compute_all_distances(nodes: &[CSVNode], edges: Vec<CSVEdge>) -> Result<DijkstrasTable, std::io::Error> {
    let mut graph_nodes: HashMap<usize, GraphNode> = HashMap::new();
    for node in nodes.iter() {
        graph_nodes.insert(node.n_id, node.get_graph());
    }

    println!("Computing adjacency matrix");

    // The adjacency table is used to show how nodes are related. If the value at i, j is None, then there is no connection. Otherwise, it represents the distance between node i, j.
    let mut adj_table: Vec<Vec<Option<f32>>> = vec![vec![None; nodes.len()]; nodes.len()];
    for edge in edges.into_iter() {
        let i = edge.source;
        let j = edge.dest;
        if i == j {
            adj_table[i][j] = Some(0.0);
            continue;
        }

        let node_a = graph_nodes.get(&i).unwrap();
        let node_b = graph_nodes.get(&j).unwrap();

        let dist = ((node_a.x + node_b.x).powi(2) + (node_a.y + node_b.y).powi(2)).sqrt();

        adj_table[i][j] = Some(dist);
        adj_table[j][i] = Some(dist);
    }

    println!("Determining destination nodes");
    /*
        We relate all nodes to all destination nodes (not path nodes)
        Therefore, our result must be all nodes in rows (one for each node), but only large enough for 
     */

    let destination_nodes: Vec<&CSVNode> = nodes.iter().filter(|x| x.is_path == 0).collect();
    let rows = graph_nodes.len();
    let cols = destination_nodes.len();

    println!("Constructing result table: {} nodes by {} destinations ({} total paths)", rows, cols, rows * cols);

    let mut result_matrix: DijkstrasTable = vec![vec![None; cols]; rows];
    for source in &graph_nodes {
        let i = *source.0;
        println!("\tMapping {i}'s destionations");

        for (j, destination) in destination_nodes.iter().enumerate() {
            if let Some(d_result) = dijkstras(i, destination.n_id, &graph_nodes, &adj_table) {
                result_matrix[i][j] = Some( (destination.n_id, d_result) )
            }
            else {
                result_matrix[i][j] = None
            }
        }
    }

    println!("Distances computation complete.");

    Ok(result_matrix)
}

fn map_sql_error(x: sqlite::Error) -> std::io::Error {
    std::io::Error::new(std::io::ErrorKind::InvalidData, x)
}

fn process_nodes(nodes: &[CSVNode], edges: Vec<CSVEdge>) -> Result<(), std::io::Error> {
    let mut result_file = File::create("./dijkstra-result.json")?;

    let result_matrix = compute_all_distances(nodes, edges)?;

    let serialized = serde_json::to_string_pretty(&result_matrix).expect("Unable to serialize");
    println!("Writing distances output to file ({} bytes)", serialized.as_bytes().len());
    result_file.write_all(serialized.as_bytes())?;
    Ok(())
}

fn db_insert(nodes: Vec<CSVNode>, tags: Vec<NodeTags>, db_path: String, create_path: String) -> Result<(), sqlite::Error> {
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

fn run(args: CommandArguments) -> Result<(), std::io::Error> {
    println!("Opening source files in './import/*'");
    let (nodes, edges, tags) = open_files()?;

    println!("Extracting information");
    let nodes: Vec<CSVNode> = csv_extract(nodes)?;
    let edges: Vec<CSVEdge> = csv_extract(edges)?;
    let tags: Vec<NodeTags> = csv_extract(tags)?;

    println!("Information extracted. {} nodes, {} edges, {} tags", nodes.len(), edges.len(), tags.len());

    if args.distances {
        println!("Begining distance computing");
        process_nodes(&nodes, edges)?;

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

    Ok( () )
}

fn main() {
    let arguments = CommandArguments::parse();
    println!("SSEB Shortest Path & Database Utility, Version 0.1.0");

    if let Err(e) = run(arguments) {
        eprintln!("{e}");
    }
}
