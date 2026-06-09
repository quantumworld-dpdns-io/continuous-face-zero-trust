FROM golang:1.22-bookworm AS builder
WORKDIR /app
COPY pkg/go/ /app/pkg/go/
COPY services/ /app/services/
RUN cd pkg/go && go mod tidy && go build ./...

FROM golang:1.22-slim AS production
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/pkg/go/ /app/pkg/go/
WORKDIR /app/pkg/go
EXPOSE 8010
ENTRYPOINT ["go", "run", "./..."]
