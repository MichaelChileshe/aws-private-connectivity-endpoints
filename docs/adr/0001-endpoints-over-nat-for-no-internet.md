# ADR 0001: VPC endpoints instead of NAT for a no-internet mandate

**Status:** Accepted
**Context:** Themba Insurance's regulator requires the claims-processing servers to have no route to the internet. The servers still depend on S3, DynamoDB, SSM, Secrets Manager, CloudWatch Logs and STS.

## Decision

Build a **private-only VPC** with no internet gateway, no NAT gateway, and no `0.0.0.0/0` route. Reach every required AWS service through a **VPC endpoint**: gateway endpoints for S3 and DynamoDB, interface endpoints for the rest.

## Options considered

**A. Private subnet behind a NAT gateway.** Rejected. NAT is outbound-only, but it is still a route to the internet. The rule is *no route*, so NAT fails the requirement regardless of how it's configured.

**B. Firewall egress filtering** (as in `aws-secure-vpc-network-firewall`). Rejected for this tier. Filtering is the right control when some internet egress is legitimate. Here none is, and the traffic to AWS services would still travel over the internet.

**C. Allow-list AWS service IP ranges.** Rejected. The ranges change constantly, the traffic stays on public paths, and a large allow-list is exactly the kind of fragile control an auditor flags.

**D. VPC endpoints with no internet route.** Chosen. Each service gets a private entry point on the AWS network. With no default route, nothing can reach the internet, whether through misconfiguration, a compromised process, or a curious engineer.

## Consequences

- The no-internet property is **structural and verifiable**: a route table with no `0.0.0.0/0`, and `curl example.com` returning `000`.
- Every service the workload needs must be anticipated. A missing endpoint means that service is simply unreachable. That's safe by default, but it creates operational work, as the `ssmmessages` trap shows.
- Private DNS and both VPC DNS attributes must be on, or interface endpoints won't be used transparently.
- Administration moves entirely to SSM Session Manager, with no SSH, bastion or inbound rules.
- Fixed cost is higher than one NAT gateway at low traffic. See [ADR 0004](0004-gateway-vs-interface-endpoints.md) and [`../cost-model.md`](../cost-model.md).
