package config

import "os"

type Config struct {
	ServiceName string
	Environment string
	RedisURL    string
	GRPCPort    string
	HTTPPort    string
}

func FromEnv() *Config {
	return &Config{
		ServiceName: getEnv("SERVICE_NAME", "cfzt-service"),
		Environment: getEnv("ENVIRONMENT", "development"),
		RedisURL:    getEnv("REDIS_URL", "redis://localhost:6379"),
		GRPCPort:    getEnv("GRPC_PORT", "50051"),
		HTTPPort:    getEnv("HTTP_PORT", "8000"),
	}
}

func getEnv(key, defaultVal string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return defaultVal
}
