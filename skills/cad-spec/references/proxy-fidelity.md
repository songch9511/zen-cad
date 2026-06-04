# Proxy Fidelity

Read this when the first CAD artifact should be a low-detail layout model.

## Principle

A layout proxy is allowed to look rough. It is not allowed to be vague about interfaces.

## May Simplify

Layout proxies may simplify:

- cosmetic fillets and chamfers;
- smooth curvature;
- fine tooth profiles;
- thread geometry;
- cable sweeps;
- surface texture;
- manufacturing reliefs;
- exact supplier body contours;
- high segment counts;
- non-interface labels or decorative detail.

## Must Preserve

Layout proxies must preserve:

- coordinate frames;
- mating planes;
- shaft and bore axes;
- mounting hole patterns;
- center distances;
- pitch circles and pitch planes;
- belt/gear/chain span envelopes;
- rail or slot travel axes;
- clearances and keep-outs;
- joint degrees of freedom;
- part transforms;
- dimensions that affect proceed review.

## Proxy Labels

Every unresolved proxy should state:

- what real item or final geometry it stands in for;
- which interfaces are trustworthy;
- which dimensions are approximate;
- what must be replaced or refined after proceed;
- whether detail modeling may change it without returning to layout review.

## Downstream Instruction

Tell CAD generators explicitly:

```text
Use low visual fidelity but high interface fidelity. Do not spend time on final fillets, accurate tooth profiles, cosmetic curves, or supplier body contours during layout. Preserve the listed locked facts exactly.
```
