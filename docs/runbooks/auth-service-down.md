# Auth Service Down — Runbook

## Detection
- Alert: `AuthFailureRateHigh` triggers
- Symptoms: 500 errors, authentication timeouts, session failures

## Impact
- Users cannot authenticate
- New sessions cannot be created
- Existing sessions continue until expiry

## Immediate Response (0-5 min)

1. **Check service health**:
   ```bash
   kubectl -n cfzt get pods -l app=auth-api
   kubectl -n cfzt logs -l app=auth-api --tail=50
   ```

2. **Check dependencies**:
   ```bash
   # Redis
   kubectl -n cfzt exec -it redis-0 -- redis-cli ping
   # Qdrant
   curl http://cfzt-qdrant:6333/healthz
   ```

3. **Check resource pressure**:
   ```bash
   kubectl -n cfzt top pods -l app=auth-api
   ```

## Short-term Mitigation (5-30 min)

1. **Restart pods**:
   ```bash
   kubectl -n cfzt rollout restart deployment/auth-api
   ```

2. **Scale up**:
   ```bash
   kubectl -n cfzt scale deployment/auth-api --replicas=5
   ```

3. **Check Redis connection pool exhaustion**:
   ```bash
   kubectl -n cfzt exec -it redis-0 -- redis-cli client list | wc -l
   ```

## Root Cause Investigation

1. Check application logs for error patterns
2. Check Redis for memory/connection issues
3. Check network policies blocking traffic
4. Check Istio proxy status
5. Review recent deployments

## Recovery

1. Verify service health returns to green
2. Verify authentication flows work end-to-end
3. Check for any stuck sessions
4. Review and update runbook if needed

## Prevention

- Set up connection pool monitoring
- Implement circuit breakers
- Regular load testing
- Capacity planning reviews
