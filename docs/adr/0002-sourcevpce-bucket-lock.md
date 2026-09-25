# ADR 0002: Pin claims data to the private path with `aws:SourceVpce`, scoped to object actions

**Status:** Accepted (revised after a teardown lockout)
**Context:** No internet protects the *server*. The claims bucket also needs protecting in its own right, so that valid credentials used from anywhere other than the claims VPC, such as a leaked key on a laptop, can't read claims data.

## Decision

Attach a bucket policy that **denies object actions** (`GetObject`, `PutObject`, `DeleteObject`, `ListBucket`) to all principals **unless `aws:SourceVpce` equals this VPC's S3 gateway endpoint ID**. Bucket-management actions are deliberately left outside the deny.

## Options considered

**A. Rely on IAM alone.** Rejected. IAM decides *who* can act, not *from where*. A leaked credential with the right permissions works from anywhere.

**B. `aws:SourceIp` condition.** Rejected. Traffic through a gateway endpoint doesn't carry a public source IP you can meaningfully pin. IP-based conditions also need range maintenance and are the weaker control.

**C. `aws:SourceVpc`.** Viable, but broader: it trusts every path in the VPC. `aws:SourceVpce` names the specific endpoint and is the tighter key.

**D. `aws:SourceVpce` deny on `s3:*`.** This was my first version, and it's **rejected**. It works during the proof, but once the endpoint is deleted the condition can never be met, and the deny blocks everyone, including the owner's admin, from even deleting the policy. Recovery needed the account root user. See [`../debugging-journey.md`](../debugging-journey.md#2--the-awssourcevpce-lock-that-locked-me-out).

**E. `aws:SourceVpce` deny on object actions only.** Chosen. The data-lock proof is identical (admin CLI gets `403`, in-VPC access works), while `PutBucketPolicy`, `DeleteBucketPolicy` and `DeleteBucket` stay available to the owner.

## Consequences

- Claims objects are readable and writable only via the claims VPC's S3 endpoint, and a stolen credential is useless elsewhere.
- Teardown must delete the bucket policy **before** emptying the bucket, because admin-side `DeleteObject` is still denied from outside the endpoint.
- General rule adopted: **any deny conditioned on something that can disappear must be checked against "can the owner still manage and delete this resource afterwards?"** before it's applied.
