# ADR 0004: Gateway endpoints where possible, interface endpoints only where required

**Status:** Accepted
**Context:** Every service the claims workload calls needs an endpoint. The two endpoint types behave, attach and bill differently.

## Decision

- Use **gateway endpoints for S3 and DynamoDB**, the only two services that offer them.
- Use **interface endpoints** only for the services the workload actually calls (`ssm`, `ssmmessages`, `ec2messages`, `secretsmanager`, `logs`, `sts`) plus the partner service.
- Turn **private DNS on** for every AWS interface endpoint.

## Comparison

| | Gateway endpoint | Interface endpoint (PrivateLink) |
|---|---|---|
| Services | S3, DynamoDB only | Most AWS services plus third-party and partner services |
| Attaches to | **Route table** (managed prefix-list route) | **Subnet** (an ENI with a private IP) and a security group |
| DNS | Public service names, routed privately | Private DNS maps the standard hostname to the ENI IP |
| Cost | **Free** | Per endpoint per AZ per hour, plus per GB |
| Reachable from on-prem / peered VPCs | No (route-table scoped) | Yes (it's an IP in the VPC) |

## Consequences

- The heaviest traffic (claims objects and records) rides the **free** gateway endpoints.
- Interface-endpoint count is the main cost driver, so each one must be justified by a real call path. Don't create "just in case" endpoints.
- Missing an interface endpoint fails closed. Missing `ssmmessages` in particular yields an instance that shows `Online` but won't open sessions (see the trap drill in [`../debugging-journey.md`](../debugging-journey.md#4--the-trap-drill-online-is-not-the-same-as-reachable)).
- Interface endpoints are AZ-specific. Production resilience means one per AZ in use, which doubles endpoint-hours for two AZs.
