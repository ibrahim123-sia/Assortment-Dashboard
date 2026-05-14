"""Deep correctness tests for MBA math and new insights endpoints.
Run against a live API on localhost:5000 with the demo store seeded."""
import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:5000/api"
ADMIN = ("admin@example.com", "Admin@12345")
DEMO = ("demo@example.com", "Demo@12345")


def call(method, path, token=None, body=None):
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, None


def login(email, pwd):
    s, p = call("POST", "/auth/login", body={"email": email, "password": pwd})
    if s != 200:
        raise RuntimeError(f"login failed: {p}")
    return p["access_token"]


passed = failed = 0

def check(name, ok, extra=""):
    global passed, failed
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}{('  ' + extra) if extra else ''}")
    if ok:
        passed += 1
    else:
        failed += 1


print("=" * 70)
print("MBA CORRECTNESS + INSIGHTS TESTS")
print("=" * 70)

print("\n[A] Login as demo manager")
token = login(*DEMO)
check("demo manager login", True)

print("\n[B] MBA math correctness")
s, p = call("GET", "/analytics/association_rules?limit=50&min_support=0.005&min_confidence=0.2", token=token)
check("association_rules returns 200", s == 200)
rules = p.get("data", [])
check("at least 1 rule returned", len(rules) > 0, f"({len(rules)} rules)")

if rules:
    rule = rules[0]
    # confidence(A->B) = support(A,B) / support(A) -- so support_ab / antecedent_support == confidence
    expected_conf = rule["support"] / rule["antecedent_support"] if rule["antecedent_support"] else 0
    diff = abs(expected_conf - rule["confidence"])
    check("confidence == support(A,B)/support(A)", diff < 0.02, f"got {rule['confidence']}, expected ~= {round(expected_conf, 3)}")

    # lift = confidence / support(B)
    expected_lift = rule["confidence"] / rule["consequent_support"] if rule["consequent_support"] else 0
    diff = abs(expected_lift - rule["lift"])
    check("lift == confidence / support(B)", diff < 0.05, f"got {rule['lift']}, expected ~= {round(expected_lift, 3)}")

    check("lift >= 1 for surfaced rules (positive association)", all(r["lift"] >= 1.0 for r in rules))
    check("all confidences in [0, 1]", all(0 <= r["confidence"] <= 1 for r in rules))
    check("all supports in [0, 1]", all(0 <= r["support"] <= 1 for r in rules))

    # rules sorted by confidence desc; ties in rounded confidence may have any lift
    # order because the underlying float sort happens before rounding to 3 decimals
    sorted_ok = all(
        rules[i]["confidence"] + 1e-3 >= rules[i + 1]["confidence"]
        for i in range(len(rules) - 1)
    )
    check("rules sorted by confidence desc (within rounding tolerance)", sorted_ok)

print("\n[C] Cross-sell recommendations")
# Pick the top product from /top_products and verify its recommendations make sense
s, p = call("GET", "/analytics/top_products?limit=1&sort_by=transactions", token=token)
top_product = p["products"][0]["description"] if p.get("products") else None
check("got a top product to test", top_product is not None, f"({top_product})")

if top_product:
    from urllib.parse import quote
    s, p = call("GET", f"/analytics/recommendations?product={quote(top_product)}&limit=5", token=token)
    check("recommendations endpoint 200", s == 200)
    check("target matched", p.get("matched") is True)
    recs = p.get("recommendations", [])
    check("returns recommendations", len(recs) > 0, f"({len(recs)} items)")
    if recs:
        check("all recommendations have lift > 0", all(r["lift"] > 0 for r in recs))
        check("all recommendations have positive co_purchase_count", all(r["co_purchase_count"] > 0 for r in recs))
        check("score = round(lift * confidence, 3)", all(
            abs(r["score"] - round(r["lift"] * r["confidence"], 3)) < 0.01 for r in recs
        ))
        check("recommendations sorted by score desc", all(
            recs[i]["score"] >= recs[i + 1]["score"] for i in range(len(recs) - 1)
        ))

print("\n[D] RFM customer segmentation")
s, p = call("GET", "/analytics/customer_segments", token=token)
check("customer_segments 200", s == 200)
segs = p.get("segments", [])
check("at least one segment", len(segs) > 0, f"({len(segs)} segments)")
total_cust = p.get("total_customers", 0)
check("total_customers > 0", total_cust > 0, f"({total_cust})")
sum_segments = sum(s["customers"] for s in segs)
check("customers across segments == total", sum_segments == total_cust, f"sum={sum_segments}, total={total_cust}")
total_share = sum(s["revenue_share"] for s in segs)
check("revenue shares sum to ~100%", 99 < total_share < 101, f"sum={round(total_share, 1)}%")

print("\n[E] Period comparison")
s, p = call("GET", "/analytics/period_comparison?period_days=30", token=token)
check("period_comparison 200", s == 200)
cur = p.get("current_period", {})
prior = p.get("prior_period", {})
check("current and prior period present", bool(cur) and bool(prior))
check("current.revenue >= 0", cur.get("revenue", -1) >= 0)
check("daily_revenue is a list", isinstance(p.get("daily_revenue"), list))

print("\n[F] Cohort retention")
s, p = call("GET", "/analytics/cohort_retention?max_periods=6", token=token)
check("cohort_retention 200", s == 200)
cohorts = p.get("cohorts", [])
check("at least one cohort", len(cohorts) > 0, f"({len(cohorts)} cohorts)")
if cohorts:
    first = cohorts[0]
    check("first cohort retention[0] == 100.0", first["retention"][0] == 100.0,
          f"got {first['retention'][0]}")
    check("retention values monotonically <= 100", all(0 <= r <= 100 for r in first["retention"]))

print("\n[G] Bundle simulator")
# Use top 2 products as a candidate bundle
s, p = call("GET", "/analytics/top_products?limit=2", token=token)
prods = [pp["description"] for pp in p.get("products", [])]
check("got two top products for simulation", len(prods) == 2)
if len(prods) == 2:
    s, p = call("POST", "/analytics/bundle_simulator", token=token, body={"products": prods, "discount_pct": 15})
    check("bundle_simulator 200", s == 200)
    check("returns current attach rate", "current" in p and "co_purchase_rate" in p["current"])
    check("returns projected revenue", "projected" in p and "projected_bundle_revenue" in p["projected"])
    check("discount_pct echoed back", p.get("discount_pct") == 15)

print("\n[H] Recommendations CSV export")
import urllib.request as ur
req = ur.Request(f"{BASE}/store/exports/csv?type=recommendations",
                 headers={"Authorization": f"Bearer {token}"})
try:
    with ur.urlopen(req, timeout=180) as r:
        ctype = r.headers.get("Content-Type", "")
        body = r.read().decode(errors="replace")
        check("CSV export 200", r.status == 200)
        check("CSV content-type", "text/csv" in ctype, ctype)
        lines = body.splitlines()
        check("CSV has header + data rows", len(lines) > 1, f"({len(lines)} lines)")
        if lines:
            cols = lines[0].split(",")
            expected = {"source_product", "recommended_product", "co_purchase_count", "confidence", "lift", "co_purchase_rate_pct", "score"}
            check("CSV has all expected columns", expected.issubset(set(cols)))
except Exception as exc:
    check("CSV export 200", False, str(exc))

print("\n" + "=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 70)
sys.exit(0 if failed == 0 else 1)
