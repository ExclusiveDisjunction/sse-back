use std::collections::HashMap;
use std::cmp::{Ord, Ordering, Eq, PartialEq};
use std::collections::BinaryHeap;
use serde::{Serialize, Deserialize};

use crate::storage::{Node, Edge};

/// A type used inside of Dijkstra's algorithm for computation steps.
#[derive(PartialEq, Debug, Clone)]
struct DijkstraHelper {
    id: usize,
    value: f32
}
impl Eq for DijkstraHelper { }
impl PartialOrd for DijkstraHelper {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}
impl Ord for DijkstraHelper {
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

/// Represents a shortest path. This includes the actual path taken, as well as the total distance.
#[derive(Serialize, Deserialize, Clone, Debug, Default, PartialEq)]
pub struct ShortestPath {
    pub points: Vec<usize>,
    pub dist: f32
}
impl Eq for ShortestPath { }
impl ShortestPath {
    fn new(points: Vec<usize>, dist: f32) -> Self {
        Self {
            points,
            dist
        }
    }
}

/// A shorthand of the result that computing all shortests paths yields.
type DijkstrasTable = Vec<Vec<Option<ShortestPath>>>;
/// The data type of an adjacency matrix.
type AdjMatrix = Vec<Vec<Option<f32>>>;

/// Using the predecesor map, determines the path taken from `src` to `dest`.
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
/// Converts a list of edges into an adjancency matrix.
fn create_adj_table(from: Vec<Edge>, nodes: &HashMap<usize, &Node>) -> AdjMatrix {
    println!("Computing adjacency matrix");

    // The adjacency table is used to show how nodes are related. If the value at i, j is None, then there is no connection. Otherwise, it represents the distance between node i, j.

    let len = nodes.len();
    let mut result: AdjMatrix = vec![vec![None; len]; len];
    for edge in from {
        let i = edge.source;
        let j = edge.dest;
        if i == j {
            result[i][j] = Some(0.0);
            continue;
        }

        let node_a = nodes.get(&i).unwrap();
        let node_b = nodes.get(&j).unwrap();

        let dist = ((node_a.x + node_b.x).powi(2) + (node_a.y + node_b.y).powi(2)).sqrt();

        result[i][j] = Some(dist);
        result[j][i] = Some(dist);
    }

    result 
}

/// Provides the graph data structure functionality. 
pub struct Graph<'a> {
    nodes: HashMap<usize, &'a Node>,
    adj: AdjMatrix
}
impl<'a> Graph<'a> {
    /// Creates the graph's information from a list of nodes and edges. 
    pub fn build(nodes: &'a [Node], edges: Vec<Edge>) -> Self {
        let mut map_nodes: HashMap<usize, &'a Node> = HashMap::new();
        for node in nodes {
            map_nodes.insert(node.n_id, node);
        }

        let adj = create_adj_table(edges, &map_nodes);

        Self {
            nodes: map_nodes,
            adj
        }
    }

    /// Computes the shortest path between the source and destionation. If no connection exists, this will return `None`.
    pub fn dijkstras(&self, source: usize, dest: usize) -> Option<ShortestPath> {
        if source == dest {
            return Some( ShortestPath::default() )
        }
    
        let mut dist: HashMap<usize, f32> = HashMap::new(); //The current distances to each node
        let mut pred: HashMap<usize, Option<usize>> = HashMap::new(); //The predecesor of the current node
        let mut visited: HashMap<usize, bool> = HashMap::new(); //If that node has already been visitied. 

        // Sets default values
        for node in self.nodes.iter() {
            dist.insert(*node.0, f32::INFINITY);
            pred.insert(*node.0, None);
            visited.insert(*node.0, false);
        }
    
        //Start at the source
        *dist.get_mut(&source).unwrap() = 0.0;
    
        let mut pq: BinaryHeap<DijkstraHelper> = BinaryHeap::new();
        pq.push(DijkstraHelper { id: source, value: 0.0 } );
    
        while !pq.is_empty() {
            // The least distance node
            let last = pq.pop().unwrap();
            let u = last.id;
    
            //Yipeee we finished
            if u == dest {
                return Some( ShortestPath::new(path_reconstruct(source, dest, pred)?, dist.get(&u).cloned()? ) )
            }
            
            if *visited.get(&u).unwrap() {
                continue;
            }
    
            // All neighbors are those inside of the adjacency table that have a non-`None` value.
            let neighbors = &self.adj[u];
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
                    pq.push(DijkstraHelper { id: v, value: new_dist });
                }
            }
        }
    
        None
    }

    /// Computes the distances between all nodes and all destination nodes.
    pub fn compute_distances(&self) -> DijkstrasTable {
        let rows = self.nodes.len();
        let cols = rows;

        println!("Constructing result table: {} nodes by {} destinations ({} total paths)", rows, cols, rows * cols);

        let mut result_matrix: DijkstrasTable = vec![vec![None; cols]; rows];
        for source in &self.nodes {
            let i = *source.0;
            println!("\tMapping {i}'s destionations");

            for dest in &self.nodes {
                let j = *dest.0;
                result_matrix[i][j] = self.dijkstras(i, j);
                
            }
        }

        println!("Distances computation complete.");

        result_matrix
    }
}