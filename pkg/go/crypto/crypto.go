package crypto

import (
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
)

func SHA256(data []byte) []byte {
	h := sha256.Sum256(data)
	return h[:]
}

func HMACSHA256(key, message []byte) []byte {
	mac := hmac.New(sha256.New, key)
	mac.Write(message)
	return mac.Sum(nil)
}

func ConstantTimeEq(a, b []byte) bool {
	return hmac.Equal(a, b)
}

func GenerateRandomBytes(n int) []byte {
	b := make([]byte, n)
	rand.Read(b)
	return b
}

func GenerateRandomString(n int) string {
	b := GenerateRandomBytes(n)
	return hex.EncodeToString(b)
}
