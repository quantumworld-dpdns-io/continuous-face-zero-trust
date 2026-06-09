use tonic::{Request, Response, Status};
use prost::Message;
use ark_bn254::{Bn254, Fr};
use ark_groth16::Groth16;
use ark_snark::SNARK;
use ark_relations::r1cs::{ConstraintSynthesizer, ConstraintSystemRef, SynthesisError};
use ark_ff::PrimeField;

mod config;
mod circuits;
mod provers;
mod verifiers;

pub mod zk_service {
    tonic::include_proto!("cfzt.zk.v1");
}

pub mod common {
    tonic::include_proto!("cfzt.common.v1");
}

#[derive(Clone)]
struct ZKServiceImpl;

#[tonic::async_trait]
impl zk_service::zk_service_server::ZkService for ZKServiceImpl {
    async fn generate_proof(
        &self,
        request: Request<zk_service::GenerateProofRequest>,
    ) -> Result<Response<zk_service::GenerateProofResponse>, Status> {
        let req = request.into_inner();
        let start = std::time::Instant::now();

        let circuit_id = req.circuit_id.clone();
        let prover_type = zk_service::ProverType::try_from(req.prover_type)
            .unwrap_or(zk_service::ProverType::Groth16);

        let proof_data = vec![0u8; 256];
        let vk_data = vec![0u8; 128];

        let elapsed = start.elapsed().as_millis() as i64;

        Ok(Response::new(zk_service::GenerateProofResponse {
            proof: proof_data,
            verification_key: vk_data,
            circuit_id,
            prover_used: prover_type.into(),
            proving_time_ms: elapsed,
            generated_at: Some(prost_types::Timestamp {
                seconds: chrono::Utc::now().timestamp(),
                nanos: 0,
            }),
        }))
    }

    async fn verify_proof(
        &self,
        request: Request<zk_service::VerifyProofRequest>,
    ) -> Result<Response<zk_service::VerifyProofResponse>, Status> {
        let req = request.into_inner();
        let start = std::time::Instant::now();
        let elapsed = start.elapsed().as_millis() as i64;

        Ok(Response::new(zk_service::VerifyProofResponse {
            valid: true,
            circuit_id: req.circuit_id,
            verification_time_ms: elapsed,
            verified_at: Some(prost_types::Timestamp {
                seconds: chrono::Utc::now().timestamp(),
                nanos: 0,
            }),
        }))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt()
        .with_env_filter("info")
        .init();

    let addr = "0.0.0.0:50053".parse()?;
    let svc = ZKServiceImpl;

    let grpc_handle = tokio::spawn({
        let svc = svc.clone();
        async move {
            tonic::transport::Server::builder()
                .add_service(zk_service::zk_service_server::ZkServiceServer::new(svc))
                .serve(addr)
                .await
                .unwrap();
        }
    });

    let app = axum::Router::new()
        .route("/health", axum::routing::get(|| async { axum::Json(serde_json::json!({"status": "ok"})) }));

    let http_addr = "0.0.0.0:8002".parse()?;
    let http_handle = tokio::spawn(async move {
        let listener = tokio::net::TcpListener::bind(http_addr).await.unwrap();
        axum::serve(listener, app).await.unwrap();
    });

    tracing::info!("ZK Proofs service started on gRPC :50053, HTTP :8002");
    tokio::join!(grpc_handle, http_handle)?;
    Ok(())
}
