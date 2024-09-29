pub mod types;

use serde_yaml::from_reader;
use std::ffi::c_char;
use std::fs::File;
use std::io::BufReader;
use types::recipe::{Recipe, ResultRecipe};

#[no_mangle]
/// パスを受け取り、レシピをパースして返す
pub extern "C" fn parse_recipe(path: *const c_char) -> ResultRecipe {
    match parse_recipe_(path) {
        Ok(recipe) => ResultRecipe {
            success: true,
            recipe,
            error_message: std::ptr::null(),
        },
        Err(e) => {
            eprintln!("{}", e);
            ResultRecipe {
                success: false,
                recipe: Recipe {
                    name: "".to_string(),
                    url: None,
                    ingredients: vec![],
                    steps: Default::default(),
                    processes: Default::default(),
                },
                error_message: std::ffi::CString::new(e).unwrap().into_raw(),
            }
        }
    }
}

fn parse_recipe_(path: *const c_char) -> Result<Recipe, String> {
    let path_str = unsafe { std::ffi::CStr::from_ptr(path).to_str().unwrap() };
    let buffer = read_yaml(path_str.to_owned()).map_err(|e| e.to_string())?;
    let recipe: Recipe = from_reader(buffer).map_err(|e| e.to_string())?;

    Ok(recipe)
}

/// YAML ファイルを読み込む
fn read_yaml(path: String) -> Result<BufReader<File>, String> {
    let file = File::open(path).map_err(|e| e.to_string())?;
    let buffer = BufReader::new(file);

    Ok(buffer)
}
