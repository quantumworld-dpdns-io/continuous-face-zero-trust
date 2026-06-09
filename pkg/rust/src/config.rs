use std::env;

#[derive(Debug, Clone)]
pub struct Config {
    pub service_name: String,
    pub environment: String,
    pub redis_url: String,
    pub qdrant_url: String,
    pub otel_endpoint: String,
    pub grpc_port: u16,
    pub http_port: u16,
}

impl Config {
    pub fn from_env() -> Self {
        Self {
            service_name: env::var("SERVICE_NAME").unwrap_or_else(|_| "cfzt-service".to_string()),
            environment: env::var("ENVIRONMENT").unwrap_or_else(|_| "development".to_string()),
            redis_url: env::var("REDIS_URL").unwrap_or_else(|_| "redis://localhost:6379".to_string()),
            qdrant_url: env::var("QDRANT_URL").unwrap_or_else(|_| "http://localhost:6333".to_string()),
            otel_endpoint: env::var("OTEL_EXPORTER_OTLP_ENDPOINT").unwrap_or_else(|_| "http://localhost:4317".to_string()),
            grpc_port: env::var("GRPC_PORT").unwrap_or_else(|_| "50051".to_string()).parse().unwrap_or(50051),
            http_port: env::var("HTTP_PORT").unwrap_or_else(|_| "8000".to_string()).parse().unwrap_or(8000),
        }
    }
}
