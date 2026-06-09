export interface Config {
  serviceName: string;
  environment: string;
  redisUrl: string;
  jwtSecret: string;
  corsOrigins: string[];
  grpcPort: number;
  httpPort: number;
}

export function getConfig(): Config {
  return {
    serviceName: process.env.SERVICE_NAME || "cfzt-edge",
    environment: process.env.ENVIRONMENT || "development",
    redisUrl: process.env.REDIS_URL || "redis://localhost:6379",
    jwtSecret: process.env.JWT_SECRET || "change-me",
    corsOrigins: (process.env.CORS_ORIGINS || "http://localhost:3000").split(","),
    grpcPort: parseInt(process.env.GRPC_PORT || "50051"),
    httpPort: parseInt(process.env.PORT || "8787"),
  };
}
