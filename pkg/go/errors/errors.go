package errors

import "fmt"

type CFZTError struct {
	Code    string
	Message string
	Status  int
}

func (e *CFZTError) Error() string {
	return fmt.Sprintf("[%s] %s", e.Code, e.Message)
}

func Unauthenticated(msg string) *CFZTError {
	return &CFZTError{Code: "UNAUTHENTICATED", Message: msg, Status: 401}
}

func Unauthorized(msg string) *CFZTError {
	return &CFZTError{Code: "UNAUTHORIZED", Message: msg, Status: 403}
}

func NotFound(msg string) *CFZTError {
	return &CFZTError{Code: "NOT_FOUND", Message: msg, Status: 404}
}

func InvalidArgument(msg string) *CFZTError {
	return &CFZTError{Code: "INVALID_ARGUMENT", Message: msg, Status: 400}
}

func Internal(msg string) *CFZTError {
	return &CFZTError{Code: "INTERNAL", Message: msg, Status: 500}
}

func RateLimited(msg string) *CFZTError {
	return &CFZTError{Code: "RATE_LIMITED", Message: msg, Status: 429}
}
