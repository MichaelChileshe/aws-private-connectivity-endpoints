# ADR 0003: PrivateLink instead of VPC peering for the partner pricing API

**Status:** Accepted
**Context:** The claims app needs a quote from SwiftRe, an external pricing partner. The no-internet rule rules out calling a public endpoint, so the connection has to be private.

## Decision

The partner publishes its pricing API as a **VPC endpoint service** (PrivateLink) behind an internal Network Load Balancer, with Themba's account as an allowed principal. Themba consumes it through an **interface endpoint** in the claims subnet.

## Options considered

**A. Partner exposes a public API; Themba calls it over the internet.** Rejected. It violates the no-internet mandate outright.

**B. VPC peering.** Rejected. Peering joins **networks**: every routable address becomes reachable in both directions (subject to SGs and routes), CIDRs must not overlap, and a compromise on the partner side has a path into the claims VPC. That's far more exposure than one API call needs.

**C. Transit Gateway attachment.** Rejected for the same reason. It's a routed network join, suited to estates Themba owns, not to a single third-party service.

**D. PrivateLink.** Chosen. It exposes **exactly one service** (the NLB listener), one way (consumer to service), with no routing between the VPCs and no concern about CIDR overlap. Access is gated by the provider's allowed-principal list, and the consumer can remove its endpoint at any time.

## Consequences

- The partner's blast radius into Themba is one TCP listener, not a network.
- The provider must front the service with an **NLB or GWLB**. An ALB can't back an endpoint service directly.
- The consumer pays for its interface endpoint (hourly plus per GB).
- In the lab the "partner" is a second VPC in the same account, and the allowed principal is that account. In production it is the partner-facing account ARN, and the provider may require manual acceptance of connection requests.
