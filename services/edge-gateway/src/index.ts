import { Hono } from "hono";
import { cors } from "hono/cors";
import { secureHeaders } from "hono/secure-headers";
import { logger } from "hono/logger";
import { requestId } from "hono/request-id";

const app = new Hono();

app.use("*", logger());
app.use("*", requestId());
app.use("*", cors());
app.use("*", secureHeaders());

app.get("/health", (c) => c.json({ status: "ok", service: "edge-gateway" }));

app.get("/api/v1/auth/health", (c) => {
  const authApiUrl = process.env.AUTH_API_URL || "http://localhost:8000";
  return c.json({ status: "ok", upstream: authApiUrl });
});

app.post("/api/v1/auth/login", async (c) => {
  const authApiUrl = process.env.AUTH_API_URL || "http://localhost:8000";
  const formData = await c.req.formData();
  const response = await fetch(`${authApiUrl}/api/v1/auth/login`, {
    method: "POST",
    body: formData,
  });
  const data = await response.json();
  return c.json(data, { status: response.status });
});

app.post("/api/v1/face/embed", async (c) => {
  const faceMlUrl = process.env.FACE_ML_URL || "http://localhost:8001";
  const body = await c.req.arrayBuffer();
  const response = await fetch(`${faceMlUrl}/api/v1/face/embed`, {
    method: "POST",
    body: body,
    headers: { "Content-Type": c.req.header("Content-Type") || "application/octet-stream" },
  });
  const data = await response.json();
  return c.json(data, { status: response.status });
});

const port = parseInt(process.env.PORT || "8787");
console.log(`Edge gateway starting on port ${port}`);

export default {
  port,
  fetch: app.fetch,
};
