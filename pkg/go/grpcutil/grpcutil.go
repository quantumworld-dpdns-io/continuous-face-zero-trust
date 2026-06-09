package grpcutil

import (
	"context"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/keepalive"
	"google.golang.org/grpc/status"
)

func NewClient(target string, opts ...grpc.DialOption) (*grpc.ClientConn, error) {
	defaultOpts := []grpc.DialOption{
		grpc.WithKeepaliveParams(keepalive.ClientParameters{
			Time:                10 * time.Second,
			Timeout:             3 * time.Second,
			PermitWithoutStream: true,
		}),
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(16*1024*1024),
			grpc.MaxCallSendMsgSize(16*1024*1024),
		),
	}
	allOpts := append(defaultOpts, opts...)
	return grpc.NewClient(target, allOpts...)
}

func IsRetryable(err error) bool {
	st, ok := status.FromError(err)
	if !ok {
		return false
	}
	switch st.Code() {
	case codes.Unavailable, codes.DeadlineExceeded, codes.ResourceExhausted:
		return true
	default:
		return false
	}
}

func WithRetry(ctx context.Context, maxRetries int, fn func() error) error {
	var lastErr error
	for i := 0; i <= maxRetries; i++ {
		if err := fn(); err != nil {
			lastErr = err
			if !IsRetryable(err) || i == maxRetries {
				return err
			}
			time.Sleep(time.Duration(1<<uint(i)) * 100 * time.Millisecond)
			continue
		}
		return nil
	}
	return lastErr
}
