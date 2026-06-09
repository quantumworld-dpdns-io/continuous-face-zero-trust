# Benchmark: Face ML Inference Latency
# Run with: cargo bench --bench inference_bench

use std::time::Instant;

fn main() {
    println!("=== CFZT Benchmarks ===\n");

    let iterations = 10000;

    // Simulated face embedding generation
    let start = Instant::now();
    for _ in 0..iterations {
        let _embedding: Vec<f32> = (0..512).map(|i| (i as f32).sin()).collect();
    }
    let elapsed = start.elapsed();
    println!("Embedding generation ({} iterations): {:?}", iterations, elapsed);
    println!("  Per inference: {:?}", elapsed / iterations as u32);

    // Simulated cosine similarity
    let a: Vec<f32> = (0..512).map(|i| (i as f32).sin()).collect();
    let b: Vec<f32> = (0..512).map(|i| (i as f32).cos()).collect();
    let start = Instant::now();
    for _ in 0..iterations {
        let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
        let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
        let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
        let _sim = dot / (norm_a * norm_b + 1e-8);
    }
    let elapsed = start.elapsed();
    println!("\nCosine similarity ({} iterations): {:?}", iterations, elapsed);
    println!("  Per comparison: {:?}", elapsed / iterations as u32);

    // Simulated HMAC-SHA256
    use sha2::{Sha256, Digest};
    let start = Instant::now();
    for _ in 0..iterations {
        let mut hasher = Sha256::new();
        hasher.update(b"test message");
        let _result = hasher.finalize();
    }
    let elapsed = start.elapsed();
    println!("\nSHA-256 hash ({} iterations): {:?}", iterations, elapsed);
    println!("  Per hash: {:?}", elapsed / iterations as u32);
}
