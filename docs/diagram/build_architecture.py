#!/usr/bin/env python3
"""Regenerates docs/architecture.svg + docs/architecture.png using the OFFICIAL AWS Architecture Icons.

The icon pack is not committed (AWS licenses it for diagrams, not redistribution). Download it from
https://aws.amazon.com/architecture/icons/, unzip, then:

    AWS_ICONS_DIR=/path/to/unzipped-icon-package python3 build_architecture.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from awsdiag import Diagram, GREY, INK

NET, STO, DB, MGMT, SEC, RED = "#8C4FFF", "#7AA116", "#C925D1", "#E7157B", "#DD344C", "#D13212"
d = Diagram(1700, 1060)

# title
d.text(1180, 38, "Themba Insurance — no-internet claims VPC", 17, "bold")
d.text(1180, 60, "VPC endpoints + PrivateLink · us-east-1", 13, "normal", GREY)

# groups
d.group("cloud", 20, 100, 1660, 945, "AWS Cloud")
d.group("region", 40, 140, 1620, 890, "Region  us-east-1")
d.group("vpc", 65, 185, 770, 820, "Claims VPC  10.70.0.0/16  ·  no internet gateway  ·  no NAT gateway")
d.group("private", 95, 245, 710, 520, "Private subnet  10.70.1.0/24  ·  us-east-1a")
d.group("vpc", 1225, 555, 420, 250, "Partner VPC  10.80.0.0/16  (SwiftRe)")

# internet — blocked
d.icon("internet", 700, 10, 50)
d.text(760, 32, "Internet", 13, "bold")
d.line([(725, 62), (725, 243)], RED, dashed=True, arrow=False)
d.block(725, 185, RED)
d.text(705, 174, "no route to 0.0.0.0/0 — curl example.com → 000", 11.5, "normal", RED, "end")

# operator -> Systems Manager
d.icon("user", 902, 10, 50)
d.text(960, 30, "Operator (Michael-admin)", 13, "bold")
d.text(960, 48, "aws ssm start-session", 12, "normal", GREY)
d.line([(926, 62), (926, 368)], MGMT, dashed=True)

# claims instance
d.icon("ec2", 150, 440, 64)
d.text(182, 524, "themba-claims-1", 13, "bold", anchor="middle")
d.text(182, 541, "t3.micro · no public IP", 11.5, "normal", GREY, "middle")
d.text(182, 557, "Session Manager only", 11.5, "normal", GREY, "middle")

# interface endpoints
d.box(380, 275, 395, 460, NET, fill="#F7F3FF")
d.text(392, 297, "Interface endpoints (PrivateLink ENIs)", 13, "bold", NET)
d.text(392, 314, "SG: 443 + 80 from 10.70.0.0/16 · private DNS on", 11.5, "normal", GREY)
for name, cy in [("ssm", 340), ("ssmmessages", 396), ("ec2messages", 452), ("secretsmanager", 508),
                 ("logs", 564), ("sts", 620), ("partner-api  (vpce-svc-…)", 676)]:
    d.icon("vpc_endpoints", 398, cy - 20, 40)
    d.text(448, cy + 5, name, 13)
d.line([(214, 472), (380, 472)], NET)
d.label(222, 462, "HTTPS 443", NET, 11)

# regional services
for key, name, sub, cy in [("ssm", "AWS Systems Manager", "Session Manager + agent", 396),
                           ("secrets", "AWS Secrets Manager", "themba/claims-db", 508),
                           ("cloudwatch", "Amazon CloudWatch Logs", "app log shipping", 564),
                           ("sts", "AWS STS", "credentials / identity", 620)]:
    d.icon(key, 900, cy - 26, 52)
    d.text(962, cy - 3, name, 13, "bold")
    d.text(962, cy + 13, sub, 11, "normal", GREY)
for cy in (340, 396, 452):
    d.line([(775, cy), (840, cy), (840, 396), (898, 396)], NET, dashed=True, arrow=(cy == 396))
for cy in (508, 564, 620):
    d.line([(775, cy), (898, cy)], NET, dashed=True)

# PrivateLink to partner
d.line([(775, 676), (1268, 676)], NET, dashed=True, width=2.5)
d.icon("privatelink", 1150, 652, 46)
d.label(900, 702, "PrivateLink — exposes ONE service, not a network", NET)
d.text(1240, 600, "VPC endpoint service · allowed principal: account", 11.5, "normal", GREY)
d.icon("nlb", 1270, 648, 56)
d.text(1298, 722, "internal NLB", 12.5, "bold", anchor="middle")
d.text(1298, 738, "TCP 80", 11, "normal", GREY, "middle")
d.icon("ec2_instance", 1470, 648, 56)
d.text(1498, 722, "pricing-api", 12.5, "bold", anchor="middle")
d.text(1498, 738, "quote JSON (ZAR)", 11, "normal", GREY, "middle")
d.line([(1326, 676), (1468, 676)], NET)

# route table + gateway endpoints
d.box(95, 790, 710, 195, STO, fill="#FAFFF0")
d.icon("vpc_router", 110, 802, 46)
d.text(168, 823, "Route table  claims-private-rt", 13, "bold")
d.text(168, 841, "10.70.0.0/16 → local", 12, "normal", GREY)
d.text(168, 858, "pl-S3 → S3 gateway endpoint   ·   pl-DynamoDB → DynamoDB gateway endpoint", 12, "normal", GREY)
d.text(168, 876, "no 0.0.0.0/0 route — ever", 12, "bold", RED)
d.icon("vpc_endpoints", 520, 893, 38)
d.text(566, 918, "S3 gateway endpoint (free)", 12)
d.icon("vpc_endpoints", 520, 938, 38)
d.text(566, 963, "DynamoDB gateway endpoint (free)", 12)
d.line([(182, 560), (182, 790)], STO)
d.label(190, 700, "S3/DynamoDB → route table", STO, 11)

# S3 + DynamoDB
d.icon("s3", 900, 885, 52)
d.text(962, 900, "Amazon S3  ·  themba-claims-private", 13, "bold")
d.text(962, 915, "bucket policy: deny object access", 11, "normal", GREY)
d.text(962, 929, "unless aws:SourceVpce = S3 endpoint", 11, "normal", GREY)
d.icon("dynamodb", 900, 952, 52)
d.text(962, 972, "Amazon DynamoDB  ·  themba-claims", 13, "bold")
d.text(962, 988, "on-demand · least-privilege item actions", 11, "normal", GREY)
d.line([(805, 912), (898, 911)], STO)
d.line([(805, 957), (898, 978)], STO)

# legend
lx, ly = 1255, 830
d.raw(f'<rect x="{lx}" y="{ly}" width="390" height="120" rx="4" fill="#fff" stroke="#D5DBDB"/>')
d.text(lx + 12, ly + 22, "Legend", 13, "bold")
d.line([(lx + 12, ly + 44), (lx + 62, ly + 44)], STO)
d.text(lx + 72, ly + 48, "gateway endpoint path (S3/DynamoDB, free)", 12)
d.line([(lx + 12, ly + 68), (lx + 62, ly + 68)], NET, dashed=True)
d.text(lx + 72, ly + 72, "interface endpoint / PrivateLink ($/hour + GB)", 12)
d.line([(lx + 12, ly + 92), (lx + 62, ly + 92)], RED, dashed=True, arrow=False)
d.text(lx + 72, ly + 96, "blocked — route does not exist", 12)

here = os.path.dirname(os.path.abspath(__file__))
d.save(os.path.join(here, "..", "architecture.svg"), os.path.join(here, "..", "architecture.png"))
print("wrote docs/architecture.svg and docs/architecture.png")
