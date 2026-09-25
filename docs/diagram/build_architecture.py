#!/usr/bin/env python3
"""Builds docs/architecture.svg (and .png via wkhtmltoimage) for aws-private-connectivity-endpoints.

Drawn in the AWS Architecture Icon style: official 2023 category colours
(Compute #ED7100, Storage #7AA116, Database #C925D1, Networking #8C4FFF,
Management #E7157B, Security #DD344C) and the standard group conventions
(AWS Cloud, Region, VPC, private subnet).

Usage:  python3 build_architecture.py            -> writes ../architecture.svg
        wkhtmltoimage --width 1700 arch.html ../architecture.png   (see bottom)
"""
import os, subprocess

W, H = 1700, 1060
FONT = "DejaVu Sans, Arial, Helvetica, sans-serif"
C = dict(compute="#ED7100", storage="#7AA116", database="#C925D1", network="#8C4FFF",
         mgmt="#E7157B", security="#DD344C", ink="#232F3E", teal="#00A4A6",
         red="#D13212", grey="#545B64")

out = []
def add(s): out.append(s)

# ---------- glyphs (white, drawn inside a 56x56 tile) ----------
def g_ec2(x, y):
    return (f'<rect x="{x+16}" y="{y+16}" width="24" height="24" fill="none" stroke="#fff" stroke-width="2.5"/>'
            + "".join(f'<line x1="{x+20+i*8}" y1="{y+10}" x2="{x+20+i*8}" y2="{y+16}" stroke="#fff" stroke-width="2.5"/>'
                      f'<line x1="{x+20+i*8}" y1="{y+40}" x2="{x+20+i*8}" y2="{y+46}" stroke="#fff" stroke-width="2.5"/>'
                      f'<line x1="{x+10}" y1="{y+20+i*8}" x2="{x+16}" y2="{y+20+i*8}" stroke="#fff" stroke-width="2.5"/>'
                      f'<line x1="{x+40}" y1="{y+20+i*8}" x2="{x+46}" y2="{y+20+i*8}" stroke="#fff" stroke-width="2.5"/>'
                      for i in range(3)))
def g_s3(x, y):
    return (f'<ellipse cx="{x+28}" cy="{y+17}" rx="15" ry="5" fill="none" stroke="#fff" stroke-width="2.5"/>'
            f'<path d="M{x+13} {y+17} L{x+17} {y+41} Q{x+28} {y+47} {x+39} {y+41} L{x+43} {y+17}" fill="none" stroke="#fff" stroke-width="2.5"/>')
def g_ddb(x, y):
    s = ""
    for dy in (14, 24, 34):
        s += f'<ellipse cx="{x+28}" cy="{y+dy}" rx="14" ry="5" fill="none" stroke="#fff" stroke-width="2.5"/>'
    s += f'<line x1="{x+14}" y1="{y+14}" x2="{x+14}" y2="{y+40}" stroke="#fff" stroke-width="2.5"/>'
    s += f'<line x1="{x+42}" y1="{y+14}" x2="{x+42}" y2="{y+40}" stroke="#fff" stroke-width="2.5"/>'
    s += f'<path d="M{x+14} {y+40} Q{x+28} {y+48} {x+42} {y+40}" fill="none" stroke="#fff" stroke-width="2.5"/>'
    return s
def g_ssm(x, y):
    s = f'<circle cx="{x+28}" cy="{y+28}" r="9" fill="none" stroke="#fff" stroke-width="2.5"/>'
    import math
    for k in range(8):
        a = k * math.pi / 4
        s += (f'<line x1="{x+28+13*math.cos(a):.1f}" y1="{y+28+13*math.sin(a):.1f}" '
              f'x2="{x+28+18*math.cos(a):.1f}" y2="{y+28+18*math.sin(a):.1f}" stroke="#fff" stroke-width="3"/>')
    return s
def g_lock(x, y):
    return (f'<rect x="{x+16}" y="{y+26}" width="24" height="18" rx="2" fill="none" stroke="#fff" stroke-width="2.5"/>'
            f'<path d="M{x+20} {y+26} V{y+19} A8 8 0 0 1 {x+36} {y+19} V{y+26}" fill="none" stroke="#fff" stroke-width="2.5"/>'
            f'<circle cx="{x+28}" cy="{y+34}" r="2.5" fill="#fff"/>')
def g_logs(x, y):
    s = f'<path d="M{x+17} {y+11} H{x+34} L{x+40} {y+17} V{y+45} H{x+17} Z" fill="none" stroke="#fff" stroke-width="2.5"/>'
    for dy in (22, 29, 36):
        s += f'<line x1="{x+22}" y1="{y+dy}" x2="{x+35}" y2="{y+dy}" stroke="#fff" stroke-width="2"/>'
    return s
def g_key(x, y):
    return (f'<circle cx="{x+20}" cy="{y+28}" r="7" fill="none" stroke="#fff" stroke-width="2.5"/>'
            f'<line x1="{x+27}" y1="{y+28}" x2="{x+44}" y2="{y+28}" stroke="#fff" stroke-width="2.5"/>'
            f'<line x1="{x+38}" y1="{y+28}" x2="{x+38}" y2="{y+34}" stroke="#fff" stroke-width="2.5"/>'
            f'<line x1="{x+43}" y1="{y+28}" x2="{x+43}" y2="{y+33}" stroke="#fff" stroke-width="2.5"/>')
def g_endpoint(x, y):
    return (f'<rect x="{x+10}" y="{y+18}" width="20" height="20" fill="none" stroke="#fff" stroke-width="2.5"/>'
            f'<line x1="{x+30}" y1="{y+28}" x2="{x+46}" y2="{y+28}" stroke="#fff" stroke-width="2.5"/>'
            f'<path d="M{x+40} {y+22} L{x+46} {y+28} L{x+40} {y+34}" fill="none" stroke="#fff" stroke-width="2.5"/>')
def g_nlb(x, y):
    return (f'<circle cx="{x+20}" cy="{y+28}" r="7" fill="none" stroke="#fff" stroke-width="2.5"/>'
            + "".join(f'<line x1="{x+27}" y1="{y+28}" x2="{x+44}" y2="{y+28+d}" stroke="#fff" stroke-width="2.5"/>'
                      for d in (-12, 0, 12)))
def g_link(x, y):
    return (f'<rect x="{x+8}" y="{y+21}" width="22" height="14" rx="7" fill="none" stroke="#fff" stroke-width="2.5"/>'
            f'<rect x="{x+26}" y="{y+21}" width="22" height="14" rx="7" fill="none" stroke="#fff" stroke-width="2.5"/>')
def g_globe(x, y):
    return (f'<circle cx="{x+28}" cy="{y+28}" r="16" fill="none" stroke="#fff" stroke-width="2.5"/>'
            f'<ellipse cx="{x+28}" cy="{y+28}" rx="7" ry="16" fill="none" stroke="#fff" stroke-width="2"/>'
            f'<line x1="{x+12}" y1="{y+28}" x2="{x+44}" y2="{y+28}" stroke="#fff" stroke-width="2"/>')
def g_user(x, y):
    return (f'<circle cx="{x+28}" cy="{y+19}" r="8" fill="none" stroke="#fff" stroke-width="2.5"/>'
            f'<path d="M{x+13} {y+45} Q{x+28} {y+24} {x+43} {y+45}" fill="none" stroke="#fff" stroke-width="2.5"/>')
def g_rt(x, y):
    return (f'<rect x="{x+11}" y="{y+13}" width="34" height="30" fill="none" stroke="#fff" stroke-width="2.5"/>'
            f'<line x1="{x+11}" y1="{y+23}" x2="{x+45}" y2="{y+23}" stroke="#fff" stroke-width="2"/>'
            f'<line x1="{x+11}" y1="{y+33}" x2="{x+45}" y2="{y+33}" stroke="#fff" stroke-width="2"/>'
            f'<line x1="{x+25}" y1="{y+13}" x2="{x+25}" y2="{y+43}" stroke="#fff" stroke-width="2"/>')

def tile(x, y, color, glyph, size=56):
    s = size / 56
    add(f'<g transform="translate({x},{y}) scale({s})"><rect x="0" y="0" width="56" height="56" rx="6" fill="{color}"/>{glyph(0,0)}</g>')

def text(x, y, t, size=13, weight="normal", color=C["ink"], anchor="start"):
    add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{t}</text>')

def group(x, y, w, h, color, label, glyph=None, dashed=False, fill="none", label_color=None):
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{color}" stroke-width="1.6"{dash}/>')
    if glyph:
        add(f'<g transform="translate({x},{y}) scale({30/56})"><rect width="56" height="56" fill="{color}"/>{glyph(0,0)}</g>')
        text(x + 38, y + 20, label, 13, "bold", label_color or color)
    else:
        text(x + 10, y + 20, label, 13, "bold", label_color or color)

def line(pts, color, dashed=False, width=2, arrow=True):
    d = "M" + " L".join(f"{a} {b}" for a, b in pts)
    dash = ' stroke-dasharray="8 6"' if dashed else ""
    mk = f' marker-end="url(#arr-{color[1:]})"' if arrow else ""
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash}{mk}/>')

def label_box(x, y, t, color=C["ink"], size=11.5):
    w = 7.2 * len(t) * size / 12 + 12
    add(f'<rect x="{x}" y="{y-13}" width="{w:.0f}" height="18" rx="3" fill="#fff" stroke="none" opacity="0.92"/>')
    text(x + 6, y, t, size, "normal", color)

# ---------- canvas ----------
add('<?xml version="1.0" encoding="UTF-8"?>')
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add("<defs>" + "".join(
    f'<marker id="arr-{c[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
    f'<path d="M0 0 L10 5 L0 10 z" fill="{c}"/></marker>' for c in (C["network"], C["storage"], C["red"], C["ink"], C["mgmt"])) + "</defs>")
add(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

# title
text(1180, 38, "Themba Insurance — no-internet claims VPC", 17, "bold")
text(1180, 60, "VPC endpoints + PrivateLink · us-east-1", 13, "normal", C["grey"])

# groups
group(20, 100, 1660, 945, C["ink"], "AWS Cloud", g_globe)
group(40, 140, 1620, 890, C["teal"], "Region  us-east-1", dashed=True)
group(65, 185, 770, 820, C["network"], "Claims VPC  10.70.0.0/16   ·   no internet gateway   ·   no NAT gateway", g_endpoint)
group(95, 245, 710, 520, C["teal"], "Private subnet  10.70.1.0/24  ·  us-east-1a", g_lock, fill="#F0FAFA")
group(1225, 555, 420, 250, C["network"], "Partner VPC  10.80.0.0/16  (SwiftRe)", g_endpoint)

# internet (blocked)
tile(700, 14, C["grey"], g_globe, 50)
text(760, 34, "Internet", 13, "bold")
line([(725, 64), (725, 240)], C["red"], dashed=True, arrow=False)
add(f'<circle cx="725" cy="185" r="13" fill="#fff" stroke="{C["red"]}" stroke-width="2.5"/>')
add(f'<path d="M718 178 L732 192 M732 178 L718 192" stroke="{C["red"]}" stroke-width="3"/>')
text(705, 174, "no route to 0.0.0.0/0 — curl example.com → 000", 11.5, "normal", C["red"], "end")

# operator -> SSM
tile(901, 14, C["grey"], g_user, 50)
text(960, 30, "Operator (Michael-admin)", 13, "bold")
text(960, 48, "aws ssm start-session", 12, "normal", C["grey"])
line([(926, 64), (926, 368)], C["mgmt"], dashed=True)

# EC2
tile(150, 440, C["compute"], g_ec2, 64)
text(182, 524, "themba-claims-1", 13, "bold", anchor="middle")
text(182, 541, "t3.micro · no public IP", 11.5, "normal", C["grey"], "middle")
text(182, 557, "SSM-managed only", 11.5, "normal", C["grey"], "middle")

# interface endpoint box
add(f'<rect x="380" y="275" width="395" height="460" rx="4" fill="#F7F3FF" stroke="{C["network"]}" stroke-width="1.2" stroke-dasharray="4 3"/>')
text(392, 297, "Interface endpoints (PrivateLink ENIs)", 13, "bold", C["network"])
text(392, 314, "SG: 443 + 80 from 10.70.0.0/16 · private DNS on", 11.5, "normal", C["grey"])
rows = [("ssm", 340), ("ssmmessages", 396), ("ec2messages", 452), ("secretsmanager", 508),
        ("logs", 564), ("sts", 620), ("partner-api  (vpce-svc-…)", 676)]
for name, cy in rows:
    tile(398, cy - 20, C["network"], g_endpoint, 40)
    text(448, cy + 5, name, 13)
line([(214, 472), (380, 472)], C["network"])
label_box(222, 462, "HTTPS 443", C["network"], 11)

# AWS services column
svc = [("Systems Manager", "Session Manager + agent", C["mgmt"], g_ssm, 396),
       ("Secrets Manager", "themba/claims-db", C["security"], g_lock, 508),
       ("CloudWatch Logs", "app log shipping", C["mgmt"], g_logs, 564),
       ("AWS STS", "credentials / identity", C["security"], g_key, 620)]
for name, sub, col, gl, cy in svc:
    tile(900, cy - 26, col, gl, 52)
    text(962, cy - 3, name, 13, "bold")
    text(962, cy + 13, sub, 11, "normal", C["grey"])
# endpoint rows -> services
for cy in (340, 396, 452):
    line([(775, cy), (840, cy), (840, 396), (898, 396)], C["network"], dashed=True, arrow=(cy == 396))
for cy in (508, 564, 620):
    line([(775, cy), (898, cy)], C["network"], dashed=True)

# PrivateLink to partner
line([(775, 676), (1268, 676)], C["network"], dashed=True, width=2.5)
tile(1150, 652, C["network"], g_link, 44)
label_box(900, 700, "PrivateLink — exposes ONE service, not a network", C["network"])

# partner VPC contents
text(1240, 600, "VPC endpoint service · allowed principal: account", 11.5, "normal", C["grey"])
tile(1270, 648, C["network"], g_nlb, 56)
text(1298, 722, "internal NLB", 12.5, "bold", anchor="middle")
text(1298, 738, "TCP 80", 11, "normal", C["grey"], "middle")
tile(1470, 648, C["compute"], g_ec2, 56)
text(1498, 722, "pricing-api", 12.5, "bold", anchor="middle")
text(1498, 738, "quote JSON (ZAR)", 11, "normal", C["grey"], "middle")
line([(1326, 676), (1468, 676)], C["network"])

# route table + gateway endpoints
add(f'<rect x="95" y="790" width="710" height="195" rx="4" fill="#FAFFF0" stroke="{C["storage"]}" stroke-width="1.2" stroke-dasharray="4 3"/>')
tile(110, 805, C["network"], g_rt, 44)
text(165, 823, "Route table  claims-private-rt", 13, "bold")
text(165, 841, "10.70.0.0/16 → local", 12, "normal", C["grey"])
text(165, 858, "pl-S3 → S3 gateway endpoint   ·   pl-DynamoDB → DynamoDB gateway endpoint", 12, "normal", C["grey"])
text(165, 876, "no 0.0.0.0/0 route — ever", 12, "bold", C["red"])
tile(520, 895, C["storage"], g_endpoint, 36)
text(564, 918, "S3 gateway endpoint (free)", 12)
tile(520, 940, C["database"], g_endpoint, 36)
text(564, 963, "DynamoDB gateway endpoint (free)", 12)
line([(182, 560), (182, 790)], C["storage"])
label_box(190, 700, "S3/DynamoDB → route table", C["storage"], 11)

# S3 + DynamoDB
tile(900, 885, C["storage"], g_s3, 52)
text(962, 900, "Amazon S3  ·  themba-claims-private", 13, "bold")
text(962, 915, "bucket policy: deny object access", 11, "normal", C["grey"])
text(962, 929, "unless aws:SourceVpce = S3 endpoint", 11, "normal", C["grey"])
tile(900, 952, C["database"], g_ddb, 52)
text(962, 972, "Amazon DynamoDB  ·  themba-claims", 13, "bold")
text(962, 988, "on-demand · least-privilege item actions", 11, "normal", C["grey"])
line([(805, 913), (898, 911)], C["storage"])
line([(805, 958), (898, 978)], C["storage"])

# legend
lx, ly = 1255, 830
add(f'<rect x="{lx}" y="{ly}" width="390" height="120" rx="4" fill="#fff" stroke="#D5DBDB"/>')
text(lx + 12, ly + 22, "Legend", 13, "bold")
line([(lx + 12, ly + 44), (lx + 62, ly + 44)], C["storage"])
text(lx + 72, ly + 48, "gateway endpoint path (S3/DynamoDB, free)", 12)
line([(lx + 12, ly + 68), (lx + 62, ly + 68)], C["network"], dashed=True)
text(lx + 72, ly + 72, "interface endpoint / PrivateLink ($ per hour + GB)", 12)
line([(lx + 12, ly + 92), (lx + 62, ly + 92)], C["red"], dashed=True, arrow=False)
text(lx + 72, ly + 96, "blocked — route does not exist", 12)

add("</svg>")

here = os.path.dirname(os.path.abspath(__file__))
svg_path = os.path.join(here, "..", "architecture.svg")
with open(svg_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
html_path = os.path.join(here, "arch.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write('<html><head><meta charset="utf-8"></head><body style="margin:0;background:#fff">' + "\n".join(out) + "</body></html>")
png_path = os.path.join(here, "..", "architecture.png")
subprocess.run(["wkhtmltoimage", "--quiet", "--width", str(W), "--height", str(H), html_path, png_path], check=False)
os.remove(html_path)
print("wrote", os.path.normpath(svg_path), "and", os.path.normpath(png_path))
