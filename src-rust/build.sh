cargo build --target wasm32-unknown-unknown --release
cp ./target/wasm32-unknown-unknown/release/deps/cooking_action_estimation.wasm ../src/correction.wasm
