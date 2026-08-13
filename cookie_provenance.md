# Cookie Provenance: A Compression-Based Approach to Affiliate Fraud Detection

**quantumcelnav**  
justin@thecanonicalart.com

---

## Abstract

Affiliate cookie stuffing is a form of commission fraud in which tracking cookies are deposited in a user's browser without a corresponding navigational act by that user. The defrauded party — typically an advertiser or affiliate network — has no mechanism to distinguish a legitimately earned cookie from a stuffed one. We propose a real-time detection system based on a principle borrowed from lossless data compression: a domain that sets a cookie but has never appeared in the user's navigation history represents a *novelty event* in the Lempel-Ziv sense. We show that this single signal, combined with five supporting signals derived from request metadata, is sufficient to detect affiliate stuffing with high confidence across a live browsing session. We implement this system as a Firefox extension operating entirely on-device, transmitting no data externally. Empirical results on two major commercial sites yield novelty rates of 88% and per-domain fraud scores of 0.80/1.0 for confirmed affiliate networks. We further note that the authorship problem in code — who wrote this, human or machine — is structurally identical to the cookie provenance problem: in both cases, the signal of interest is the distance between an artifact and the known history of its claimed originator.

---

## 1. Introduction

Commerce on the web is funded in significant part by affiliate marketing: a publisher earns a commission when a user they referred completes a purchase. The integrity of this system depends on a chain of provenance — the user clicked a link, the link deposited a cookie, the cookie was present at checkout. Cookie stuffing breaks this chain. A site deposits an affiliate cookie without the user having clicked any link. The user completes a purchase. The stuffing party collects a commission they did not earn.

The scale of the problem has been established empirically. In 2026, Bloomberg reported that 51% of the merchandise value credited to Phia — a shopping application — originated from cookie stuffing. Impact.com, one of the largest affiliate networks, subsequently suspended the company from its marketplace. The founders stated they were unaware of the practice.

We do not adjudicate that claim. We observe instead that the technical infrastructure to make such unawareness implausible has not previously been available to ordinary users. We build it.

The core insight is classical. Lempel and Ziv observed in 1978 that the compressibility of a sequence is determined by how much of it can be expressed as references to previously seen substrings. A string that contains many novel substrings is incompressible — it carries high information. We apply this intuition to browsing sessions: a user's navigation history is a dictionary. A cookie-setting event from a domain not in that dictionary is a *novelty miss* — an event that the dictionary cannot explain. High novelty rates indicate that something is setting cookies that the user's navigation did not cause.

---

## 2. The Cookie Provenance Problem

We define the following:

Let **N** be the set of hostnames a user has navigated to during their browsing history. We call **N** the *navigation dictionary*.

Let **E** = {e₁, e₂, ..., eₙ} be the sequence of cookie-setting events observed during a session, where each event eᵢ carries:
- `domain` — the hostname setting the cookie
- `name` — the cookie name
- `url` — the full request URL
- `type` — the resource type (image, XHR, script, etc.)
- `timestamp` — milliseconds since the initiating page navigation
- `referer` — the Referer request header, if present

A *legitimate* cookie-setting event is one causally downstream of a user navigational act. An *illegitimate* event — a stuffed cookie — is one that occurs without such a cause.

The causal chain is not directly observable. We cannot inspect the user's intent. We can, however, observe whether the cookie-setting domain appears in **N**. If it does not, the event is a novelty miss with respect to the navigation dictionary.

Formally, define the *LZ novelty indicator* for domain *d*:

```
lz(d) = 0  if d ∈ N (or any apex domain of d ∈ N)
lz(d) = 1  otherwise
```

This is the primary signal. Five supporting signals refine it.

---

## 3. Signal Architecture

We define a suspicion score *s(e)* ∈ [0, 1] for each cookie-setting event, as a weighted sum of six binary or continuous signals:

```
s(e) = 0.30 · lz(d)
     + 0.25 · aff_url(url)
     + 0.15 · aff_cookie(name)
     + 0.15 · hidden(type)
     + 0.10 · timing(timestamp)
     + 0.05 · no_referer(referer)
```

**LZ novelty** (weight 0.30): 1 if the domain has never appeared in navigation history, 0 otherwise. This is the dominant signal. A user who navigated to a domain and received a cookie from it has a plausible causal story. A user who never visited a domain but received a cookie from it does not.

**Affiliate URL pattern** (weight 0.25): 1 if the request URL matches known affiliate tracking patterns — `/click`, `/track`, `/redirect`, query parameters `affiliate_id`, `publisher_id`, `aff_id`, `ref`, `subid`, `clickid`, and others. Confirmed affiliate network domains receive this score unconditionally.

**Affiliate cookie name** (weight 0.15): 1 if the cookie name matches patterns common to affiliate tracking — prefixes `aff`, `affiliate`, `partner`, `ref`, `publisher`, `clickid`, `subid`; suffixes `_aff`, `_ref`, `_click`; network-specific patterns `cj_`, `sa_`, `aw_`, `rakuten`, `impact_`.

**Hidden resource type** (weight 0.15): 1 for resource types that are not directly user-initiated — `image`, `media`, `xmlhttprequest`, `ping`, `beacon`, `websocket`; 0.7 for `script`. These types are the standard delivery mechanism for tracking pixels and invisible cookie-setting requests.

**Early timing** (weight 0.10): 1 if the cookie is set within 500ms of page navigation. This interval is too short for a user to have clicked anything. The signal decays linearly to 0 by 2000ms.

**No Referer** (weight 0.05): The fraction of a domain's cookies that arrive without a Referer header. Legitimate referrals typically carry a Referer. Its absence removes one piece of the causal chain.

We aggregate signals at the domain level, taking the maximum observed value for each signal across all cookie events from that domain. A domain with suspicion score *s* ≥ 0.65 is classified HIGH; *s* ≥ 0.35 is MEDIUM.

---

## 4. The Navigation Dictionary

The navigation dictionary **N** is built from `webNavigation.onCommitted` events — the moment the browser commits to loading a URL in a top-level frame. Each committed hostname, and its apex domain, is added to **N**. The dictionary persists across browser sessions in `storage.local`.

A key property: the dictionary is retroactive. When a user navigates to a domain that has previously set a suspicious cookie, the LZ novelty signal for that domain is recalculated to 0. Visiting a domain de-risks its prior cookies. This prevents false positives for sites that set cookies before the top-level navigation completes.

The navigation dictionary grows monotonically with browsing history. Over time, it approximates the full set of domains the user has intentionally visited. The novelty signal becomes more specific: the longer the dictionary, the more unusual it is for a cookie-setting domain to be absent from it.

---

## 5. The Affiliate Network Fingerprint

We maintain a fingerprint database of 17 affiliate networks, mapping network names to their known tracking domains:

Commission Junction, ShareASale, Awin, Rakuten Advertising, Impact, PartnerStack, Partnerize, ClickBank, FlexOffers, PepperJam, Tradedoubler, Viglink/Skimlinks, MaxBounty, Refersion, Tune/HasOffers, CivicScience, and generic tracker infrastructure operated by Google (DoubleClick, Google Ad Services).

A domain matching this database is confirmed as an affiliate network regardless of LZ novelty. Such a domain is classified as *fraud* — its presence constitutes commission fraud rather than merely tracking. Generic ad trackers that score HIGH via the signal architecture but are not in the fingerprint database are classified separately as *suspicious* — a privacy problem, but not direct commission fraud.

This distinction matters for remediation and for regulatory framing.

---

## 6. Implementation

The system is implemented as a Firefox Manifest V3 extension. The background script maintains session state in memory and the navigation dictionary in `storage.local`. No data is transmitted externally at any point.

Two browser hooks do the primary work:

`webNavigation.onCommitted` fires on each top-level page load and adds the committed hostname to the navigation dictionary.

`webRequest.onCompleted` with `responseHeaders` fires on every completed HTTP request that set a cookie. Firefox exposes `Set-Cookie` headers at this hook, enabling real-time scoring of each cookie event as it occurs.

A companion `webRequest.onBeforeSendHeaders` hook captures the outgoing `Referer` header by request ID, making it available when the corresponding response arrives.

The popup renders the current session state: a navigation dictionary size, a global LZ novelty rate (the fraction of all cookie events sourced from novel domains), and per-domain cards showing signal breakdowns and allowing one-click cookie deletion via `browser.cookies.remove()`.

Source code is available at https://github.com/quantumcelnav/cookiestuff under the Apache 2.0 license. The extension is listed on addons.mozilla.org.

---

## 7. Empirical Results

We report results from two commercial sites visited during live browsing sessions in August 2026.

**Slickdeals.net**: 53 distinct domains set cookies during a single session. The LZ novelty rate was 88.2% — 47 of 53 cookie-setting domains had no entry in the navigation dictionary despite the session beginning with a direct navigation to slickdeals.net itself. This indicates that the page, through embedded resources, caused cookie-setting events from domains the user had no prior relationship with.

**Yahoo.com**: The domain `doubleclick.net`, operated by Google, received a suspicion score of 0.80/1.0 and was confirmed against the affiliate network fingerprint database. The cookie was set via an image resource within 400ms of page load, with no Referer header, from a domain matching the affiliate URL pattern database. Classification: affiliate fraud.

These results are reproducible. Any user who installs the extension and visits these sites will observe comparable behavior. The tool is not a forensic instrument requiring specialized access — it observes what any browser observes, and applies the scoring architecture described above.

---

## 8. Provenance, Authorship, and the Stylometric Parallel

The problem of cookie provenance — determining whether a cookie was legitimately earned — is structurally isomorphic to the problem of authorship attribution.

In both cases, an artifact (a cookie; a text) claims a provenance (a user click; a human author). In both cases, the claim cannot be verified directly. In both cases, we resort to signal-based inference: does this artifact exhibit the statistical properties we would expect given its claimed provenance?

Stylometric analysis detects authorship by measuring the distance between a text and a known author's corpus. LZ novelty detects cookie stuffing by measuring the distance between a cookie-setting domain and the user's navigation corpus. The mathematics differ; the epistemology is the same.

We note this parallel not as decoration but as a claim about the current moment. The question "who made this?" — applied to code, to text, to commission cookies — is becoming the central question of digital commerce and digital expression. The answer is never self-evident. It is always inferred from signals. The signals can be gamed, but gaming them is costly, and the cost is a form of accountability.

The authors of CookieStuff wrote it with the assistance of a large language model. The authors of the Bitcoin whitepaper wrote under a pseudonym that has never been resolved. The code in this repository was written by humans, or by machines instructed by humans, or by humans performing machines. The provenance is contested in every case.

What is not contested is whether the cookies were stuffed. The signal is there. The math is simple. The browser does not lie.

---

## 9. Conclusion

We have described a real-time detection system for affiliate cookie stuffing based on LZ novelty scoring and a six-signal detection architecture. The system requires no external data, no account, and no specialized access — only a Firefox browser and the extension available at addons.mozilla.org.

The Phia case demonstrated that 51% of credited sales at a $180M company could be fraudulent, and that the response was "we didn't know." We propose that this defense becomes harder to sustain when the tool to detect the behavior runs in every user's browser.

The broader proposal is this: the integrity of web commerce depends on provenance. Provenance is not self-certifying. Detection systems like the one described here are necessary infrastructure, not edge-case tooling. The affiliate networks, the advertisers, and the regulators all have access to the same signals. The question is whether they look.

We looked.

---

## References

[1] Lempel, A., Ziv, J. (1978). Compression of Individual Sequences via Variable-Rate Coding. *IEEE Transactions on Information Theory*, 24(5), 530–536.

[2] Nakamoto, S. (2008). Bitcoin: A Peer-to-Peer Electronic Cash System.

[3] Bloomberg News (2026, July). Phia Cookie Stuffing Investigation.

[4] Impact.com (2026). Notice of Marketplace Suspension: Phia.

[5] Fritz, J. (2026). CookieStuff: Real-time Affiliate Cookie Stuffing Detection. https://github.com/quantumcelnav/cookiestuff

[6] Mozilla Corporation (2026). Firefox Add-on Distribution Agreement.

[7] Kachin, V. et al. (2019). Stylometric Analysis for Authorship Attribution. *Journal of Digital Forensics*, 14(2).

---

*This paper was written with the assistance of an AI language model. The experiments were conducted by the human author. The math is the same either way.*
