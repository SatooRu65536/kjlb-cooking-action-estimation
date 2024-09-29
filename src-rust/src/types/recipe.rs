use serde::{Deserialize, Serialize};
use std::{collections::HashMap, ffi::c_char};

type ID = String;

#[derive(Serialize, Deserialize, Debug)]
pub struct Ingredient {
    name: String,
    quantity: f64,
    unit: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Process {
    title: String,
    description: String,
    time: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Recipe {
    pub name: String,
    pub url: Option<String>,
    pub ingredients: Vec<Ingredient>,
    pub steps: HashMap<ID, Option<Process>>,
    pub processes: HashMap<ID, Process>,
}

#[repr(C)]
pub struct ResultRecipe {
    pub success: bool,
    pub recipe: Recipe,
    pub error_message: *const c_char, // エラーメッセージを格納するためのポインタ
}
