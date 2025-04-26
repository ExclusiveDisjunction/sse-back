use serde::{Serialize, Deserialize};

/// Represents a node pulled out of the CSV file, and will be imported into the database.
#[derive(Serialize, Deserialize, Debug, PartialEq, Clone)]
pub struct Node {
    pub n_id: usize,
    pub x: f32,
    pub y: f32,
    pub name: String,
    pub group: String,
    pub is_path: i8
}

/// Represents a edge connecting two nodes from the CSV file.
#[derive(Serialize, Deserialize, Debug, PartialEq, Eq, Clone)]
pub struct Edge {
    pub source: usize,
    pub dest: usize
}

/// Represents a tag applied to a specific node.
#[derive(Serialize, Deserialize, Debug, PartialEq, Eq, Clone)]
pub struct NodeTags {
    pub n_id: usize,
    pub tag: String
}