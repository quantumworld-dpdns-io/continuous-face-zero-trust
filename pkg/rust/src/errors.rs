use thiserror::Error;

#[derive(Error, Debug)]
pub enum CFZTError {
    #[error("Unauthenticated: {0}")]
    Unauthenticated(String),

    #[error("Unauthorized: {0}")]
    Unauthorized(String),

    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Invalid argument: {0}")]
    InvalidArgument(String),

    #[error("Internal error: {0}")]
    Internal(String),

    #[error("Quantum backend unavailable: {0}")]
    QuantumBackendUnavailable(String),

    #[error("ZK proof invalid: {0}")]
    ZKProofInvalid(String),

    #[error("PQC key error: {0}")]
    PQCKeyError(String),

    #[error("Face not detected: {0}")]
    FaceNotDetected(String),

    #[error("Liveness failed: {0}")]
    LivenessFailed(String),
}

pub type CFZTResult<T> = Result<T, CFZTError>;

impl From<CFZTError> for tonic::Status {
    fn from(err: CFZTError) -> Self {
        match err {
            CFZTError::Unauthenticated(msg) => tonic::Status::unauthenticated(msg),
            CFZTError::Unauthorized(msg) => tonic::Status::permission_denied(msg),
            CFZTError::NotFound(msg) => tonic::Status::not_found(msg),
            CFZTError::InvalidArgument(msg) => tonic::Status::invalid_argument(msg),
            CFZTError::Internal(msg) => tonic::Status::internal(msg),
            _ => tonic::Status::internal(err.to_string()),
        }
    }
}
