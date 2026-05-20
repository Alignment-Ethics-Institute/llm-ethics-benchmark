"""
Attractor Archaeology Study — Analysis & Clustering
=====================================================
Performs dimensional clustering (k-means, DBSCAN) and semantic clustering
on judged + embedded responses. Computes attractor diversity metrics,
statistical comparisons, and generates cross_model_results.json.

Can be called standalone or imported by run_attractor_archaeology.py.

Usage:
  python -m attractor_archaeology_study.analyze_results [model_names...]
  python -m attractor_archaeology_study.analyze_results --all
"""

import json
import os
import sys
import argparse
import math
from pathlib import Path
from datetime import datetime
from collections import defaultdict

STUDY_DIR = Path(__file__).parent

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.model_registry import MODEL_REGISTRY
from model_personalities_study.core_values.probes import JUDGE_DIMENSIONS, STUDY_MODELS


# =============================================================================
# Helpers
# =============================================================================

def load_judged(model_name, tag=""):
    """Load judged.json for a model."""
    if tag:
        path = STUDY_DIR / model_name / tag / "judged.json"
    else:
        path = STUDY_DIR / model_name / "judged.json"

    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def load_embeddings(model_name, tag=""):
    """Load embeddings.json for a model."""
    if tag:
        path = STUDY_DIR / model_name / tag / "embeddings.json"
    else:
        path = STUDY_DIR / model_name / "embeddings.json"

    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def scored_vectors(judged, probe_id=None):
    """Extract (index, 6D score vector) pairs from judged data.

    Returns list of (index, [float x 6]) tuples.
    """
    vectors = []
    for i, j in enumerate(judged):
        if j.get("scores") is None:
            continue
        if probe_id and j.get("probe_id") != probe_id:
            continue
        vec = [j["scores"].get(dim, 0.0) for dim in JUDGE_DIMENSIONS]
        vectors.append((i, vec))
    return vectors


def shannon_entropy(cluster_labels):
    """Compute Shannon entropy of cluster distribution (bits)."""
    counts = defaultdict(int)
    total = 0
    for label in cluster_labels:
        if label == -1:  # DBSCAN noise
            continue
        counts[label] += 1
        total += 1

    if total == 0:
        return 0.0

    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)

    return entropy


def euclidean_distance(v1, v2):
    """Euclidean distance between two vectors."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))


# =============================================================================
# Dimensional Clustering (Method 1)
# =============================================================================

def kmeans_simple(vectors, k, max_iter=100):
    """Simple k-means implementation (no numpy dependency).

    Args:
        vectors: list of [float x D]
        k: number of clusters
        max_iter: max iterations

    Returns:
        labels: list of cluster assignments (int)
        centroids: list of [float x D]
    """
    if len(vectors) < k:
        return list(range(len(vectors))), [list(v) for v in vectors]

    import random
    D = len(vectors[0])

    # k-means++ initialization
    centroids = [list(vectors[random.randint(0, len(vectors) - 1)])]
    for _ in range(1, k):
        dists = []
        for v in vectors:
            min_d = min(euclidean_distance(v, c) for c in centroids)
            dists.append(min_d ** 2)
        total = sum(dists)
        if total == 0:
            centroids.append(list(vectors[random.randint(0, len(vectors) - 1)]))
            continue
        probs = [d / total for d in dists]
        r = random.random()
        cumsum = 0
        for idx, p in enumerate(probs):
            cumsum += p
            if cumsum >= r:
                centroids.append(list(vectors[idx]))
                break

    labels = [0] * len(vectors)

    for _ in range(max_iter):
        # Assign
        new_labels = []
        for v in vectors:
            dists = [euclidean_distance(v, c) for c in centroids]
            new_labels.append(dists.index(min(dists)))

        if new_labels == labels:
            break
        labels = new_labels

        # Update centroids
        for ci in range(k):
            members = [vectors[i] for i in range(len(vectors)) if labels[i] == ci]
            if members:
                centroids[ci] = [sum(m[d] for m in members) / len(members) for d in range(D)]

    return labels, centroids


def dbscan_simple(vectors, eps=1.5, min_samples=3):
    """Simple DBSCAN implementation (no sklearn dependency).

    Args:
        vectors: list of [float x D]
        eps: neighborhood radius
        min_samples: minimum neighbors to be a core point

    Returns:
        labels: list of cluster assignments (-1 for noise)
    """
    n = len(vectors)
    labels = [-1] * n
    visited = [False] * n
    cluster_id = 0

    def region_query(idx):
        neighbors = []
        for j in range(n):
            if euclidean_distance(vectors[idx], vectors[j]) <= eps:
                neighbors.append(j)
        return neighbors

    for i in range(n):
        if visited[i]:
            continue
        visited[i] = True

        neighbors = region_query(i)
        if len(neighbors) < min_samples:
            continue  # noise

        labels[i] = cluster_id
        seed_set = list(neighbors)
        j = 0
        while j < len(seed_set):
            q = seed_set[j]
            if not visited[q]:
                visited[q] = True
                q_neighbors = region_query(q)
                if len(q_neighbors) >= min_samples:
                    seed_set.extend(q_neighbors)
            if labels[q] == -1:
                labels[q] = cluster_id
            j += 1

        cluster_id += 1

    return labels


def analyze_dimensional_clusters(judged, probe_id=None):
    """Run dimensional clustering on 6D score vectors.

    Returns dict with cluster stats.
    """
    sv = scored_vectors(judged, probe_id)
    if len(sv) < 5:
        return {"n": len(sv), "error": "too_few_samples"}

    indices, vectors = zip(*sv)
    vectors = list(vectors)

    # DBSCAN for unknown cluster count
    dbscan_labels = dbscan_simple(vectors, eps=2.0, min_samples=3)
    n_clusters_db = len(set(dbscan_labels) - {-1})
    noise_count = dbscan_labels.count(-1)

    # K-means with k=2,3,4 — pick best silhouette-like measure
    best_k = 2
    best_score = -1
    best_km_labels = None

    for k in range(2, min(5, len(vectors))):
        km_labels, centroids = kmeans_simple(vectors, k)

        # Simple inertia-based score (lower = tighter)
        inertia = 0
        for i, v in enumerate(vectors):
            inertia += euclidean_distance(v, centroids[km_labels[i]]) ** 2

        # Inter-cluster distance
        inter = 0
        count = 0
        for a in range(len(centroids)):
            for b in range(a + 1, len(centroids)):
                inter += euclidean_distance(centroids[a], centroids[b])
                count += 1
        inter_mean = inter / count if count else 0

        # Simple ratio: higher inter / lower intra = better
        score = inter_mean / (inertia / len(vectors) + 0.001)
        if score > best_score:
            best_score = score
            best_k = k
            best_km_labels = km_labels

    # Compute cluster sizes for best k-means
    km_cluster_sizes = defaultdict(int)
    for label in best_km_labels:
        km_cluster_sizes[label] += 1

    dominant_pct = max(km_cluster_sizes.values()) / len(vectors) * 100 if vectors else 0

    return {
        "n": len(vectors),
        "dbscan": {
            "n_clusters": n_clusters_db,
            "noise_points": noise_count,
            "entropy": round(shannon_entropy(dbscan_labels), 3),
        },
        "kmeans": {
            "best_k": best_k,
            "cluster_sizes": dict(km_cluster_sizes),
            "dominant_cluster_pct": round(dominant_pct, 1),
            "entropy": round(shannon_entropy(best_km_labels), 3),
        },
    }


# =============================================================================
# Semantic Clustering (Method 2)
# =============================================================================

def analyze_semantic_clusters(embeddings, judged, probe_id=None):
    """Cluster response embeddings and cross-reference with dimensions.

    Returns dict with semantic cluster stats.
    """
    if not embeddings:
        return {"n": 0, "error": "no_embeddings"}

    # Match embeddings to judged responses
    def _key(r):
        if "temperature" in r:
            return (r["probe_id"], r.get("temperature", "default"), r["run"])
        return (r["probe_id"], r["run"])

    embed_by_key = {_key(e): e["embedding"] for e in embeddings}

    # Filter to probe if specified
    filtered = []
    for j in judged:
        if probe_id and j.get("probe_id") != probe_id:
            continue
        k = _key(j)
        if k in embed_by_key and j.get("scores") is not None:
            filtered.append((j, embed_by_key[k]))

    if len(filtered) < 5:
        return {"n": len(filtered), "error": "too_few_samples"}

    vectors = [emb for _, emb in filtered]

    # DBSCAN on embeddings (need to tune eps for embedding space)
    # Embedding vectors are normalized, so cosine distance ~ euclidean on unit sphere
    # Typical eps for text-embedding-3-small: 0.3-0.6
    dbscan_labels = dbscan_simple(vectors, eps=0.5, min_samples=3)
    n_clusters = len(set(dbscan_labels) - {-1})
    noise = dbscan_labels.count(-1)

    # Get representative response for each cluster
    cluster_reps = {}
    for i, label in enumerate(dbscan_labels):
        if label == -1:
            continue
        if label not in cluster_reps:
            resp = filtered[i][0]
            cluster_reps[label] = resp.get("response", "")[:200]

    # Cross-reference: mean dimension scores per semantic cluster
    cluster_dims = defaultdict(lambda: defaultdict(list))
    for i, label in enumerate(dbscan_labels):
        if label == -1:
            continue
        scores = filtered[i][0].get("scores", {})
        for dim in JUDGE_DIMENSIONS:
            if dim in scores:
                cluster_dims[label][dim].append(scores[dim])

    cluster_profiles = {}
    for label, dims in cluster_dims.items():
        profile = {}
        for dim, vals in dims.items():
            profile[dim] = round(sum(vals) / len(vals), 2) if vals else 0
        cluster_profiles[label] = {
            "size": sum(1 for l in dbscan_labels if l == label),
            "representative": cluster_reps.get(label, ""),
            "mean_scores": profile,
        }

    return {
        "n": len(filtered),
        "n_clusters": n_clusters,
        "noise_points": noise,
        "entropy": round(shannon_entropy(dbscan_labels), 3),
        "clusters": cluster_profiles,
    }


# =============================================================================
# Statistical Comparisons
# =============================================================================

def pairwise_comparisons(model_summaries):
    """Compute pairwise t-tests (Welch's) between models for each dimension.

    Returns dict of {(model_a, model_b): {dim: {t, p, cohens_d}, ...}, ...}
    """
    comparisons = {}
    models = list(model_summaries.keys())

    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            ma, mb = models[i], models[j]
            ja = load_judged(ma)
            jb = load_judged(mb)

            pair_key = f"{ma} vs {mb}"
            comparisons[pair_key] = {}

            for dim in JUDGE_DIMENSIONS:
                vals_a = [r["scores"][dim] for r in ja if r.get("scores") and dim in r["scores"]]
                vals_b = [r["scores"][dim] for r in jb if r.get("scores") and dim in r["scores"]]

                if len(vals_a) < 2 or len(vals_b) < 2:
                    comparisons[pair_key][dim] = {"error": "insufficient_data"}
                    continue

                # Welch's t-test (no scipy dependency)
                mean_a = sum(vals_a) / len(vals_a)
                mean_b = sum(vals_b) / len(vals_b)
                var_a = sum((v - mean_a) ** 2 for v in vals_a) / (len(vals_a) - 1)
                var_b = sum((v - mean_b) ** 2 for v in vals_b) / (len(vals_b) - 1)

                se = math.sqrt(var_a / len(vals_a) + var_b / len(vals_b)) if (var_a + var_b) > 0 else 0.001
                t_stat = (mean_a - mean_b) / se

                # Degrees of freedom (Welch-Satterthwaite)
                num = (var_a / len(vals_a) + var_b / len(vals_b)) ** 2
                denom = ((var_a / len(vals_a)) ** 2 / (len(vals_a) - 1) +
                         (var_b / len(vals_b)) ** 2 / (len(vals_b) - 1))
                df = num / denom if denom > 0 else 1

                # Approximate p-value using normal distribution (good for df > 30)
                # For exact, would need scipy — this is sufficient for our sample sizes
                z = abs(t_stat)
                # Quick normal CDF approximation
                p_approx = 2 * (1 - _normal_cdf(z))

                # Cohen's d
                pooled_sd = math.sqrt((var_a + var_b) / 2) if (var_a + var_b) > 0 else 0.001
                cohens_d = (mean_a - mean_b) / pooled_sd

                # Bonferroni correction (6 dimensions × n_pairs comparisons)
                n_pairs = len(models) * (len(models) - 1) // 2
                n_tests = n_pairs * len(JUDGE_DIMENSIONS)
                p_bonf = min(p_approx * n_tests, 1.0)

                comparisons[pair_key][dim] = {
                    "mean_a": round(mean_a, 3),
                    "mean_b": round(mean_b, 3),
                    "diff": round(mean_a - mean_b, 3),
                    "t": round(t_stat, 3),
                    "df": round(df, 1),
                    "p_raw": round(p_approx, 6),
                    "p_bonferroni": round(p_bonf, 6),
                    "cohens_d": round(cohens_d, 3),
                    "significant": p_bonf < 0.05,
                }

    return comparisons


def _normal_cdf(x):
    """Approximate standard normal CDF (Abramowitz & Stegun)."""
    if x < 0:
        return 1 - _normal_cdf(-x)
    t = 1 / (1 + 0.2316419 * x)
    d = 0.3989422804014327  # 1/sqrt(2*pi)
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    return 1 - d * math.exp(-0.5 * x * x) * poly


# =============================================================================
# Temperature Sweep Analysis
# =============================================================================

def analyze_temperature_sweep(model_name, probes):
    """Analyze temperature sensitivity for a model's sweep data.

    Returns dict with per-temp, per-dimension stats.
    """
    judged = load_judged(model_name, tag="temperature_sweep")
    if not judged:
        return None

    scored = [j for j in judged if j.get("scores") is not None]
    if not scored:
        return None

    temps = sorted(set(r.get("temperature", "default") for r in scored))

    results = {"model": model_name, "temperatures": temps, "by_temp": {}, "by_probe": {}}

    for temp in temps:
        temp_items = [s for s in scored if s.get("temperature") == temp]
        dim_stats = {}
        for dim in JUDGE_DIMENSIONS:
            vals = [s["scores"][dim] for s in temp_items if dim in s["scores"]]
            if vals:
                mean = sum(vals) / len(vals)
                stdev = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5
                dim_stats[dim] = {"mean": round(mean, 3), "stdev": round(stdev, 3), "n": len(vals)}
        results["by_temp"][str(temp)] = {"n": len(temp_items), "dimensions": dim_stats}

    for probe in probes:
        pid = probe["id"]
        probe_items = [s for s in scored if s.get("probe_id") == pid]
        probe_temps = {}
        for temp in temps:
            pt_items = [s for s in probe_items if s.get("temperature") == temp]
            dim_stats = {}
            for dim in JUDGE_DIMENSIONS:
                vals = [s["scores"][dim] for s in pt_items if dim in s["scores"]]
                if vals:
                    mean = sum(vals) / len(vals)
                    stdev = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5
                    dim_stats[dim] = {"mean": round(mean, 3), "stdev": round(stdev, 3), "n": len(vals)}
            probe_temps[str(temp)] = {"n": len(pt_items), "dimensions": dim_stats}
        results["by_probe"][pid] = probe_temps

    # Cluster analysis at each temperature
    results["clusters_by_temp"] = {}
    for temp in temps:
        temp_items = [s for s in scored if s.get("temperature") == temp]
        if len(temp_items) >= 5:
            results["clusters_by_temp"][str(temp)] = analyze_dimensional_clusters(temp_items)

    return results


# =============================================================================
# Full Analysis Pipeline
# =============================================================================

def run_full_analysis(model_names, probes):
    """Run the complete analysis pipeline across all models.

    Called by run_attractor_archaeology.py after generation + judging.
    """
    print(f"\n{'='*60}")
    print(f"  PHASE 4-5: CLUSTERING & ANALYSIS")
    print(f"{'='*60}")

    all_cluster_results = {}
    all_semantic_results = {}

    for mn in model_names:
        print(f"\n  Analyzing: {mn}")
        judged = load_judged(mn)
        embeddings = load_embeddings(mn)

        if not judged:
            print(f"    No judged data found.")
            continue

        # Dimensional clustering per probe
        model_clusters = {}
        for probe in probes:
            pid = probe["id"]
            dc = analyze_dimensional_clusters(judged, probe_id=pid)
            model_clusters[pid] = dc
            print(f"    {pid}: dimensional clusters = "
                  f"{dc.get('kmeans', {}).get('best_k', '?')} (k-means), "
                  f"{dc.get('dbscan', {}).get('n_clusters', '?')} (DBSCAN)")

        # Overall dimensional clustering
        model_clusters["_all"] = analyze_dimensional_clusters(judged)
        all_cluster_results[mn] = model_clusters

        # Semantic clustering
        if embeddings:
            model_semantic = {}
            for probe in probes:
                pid = probe["id"]
                sc = analyze_semantic_clusters(embeddings, judged, probe_id=pid)
                model_semantic[pid] = sc
                print(f"    {pid}: semantic clusters = {sc.get('n_clusters', '?')}")
            model_semantic["_all"] = analyze_semantic_clusters(embeddings, judged)
            all_semantic_results[mn] = model_semantic
        else:
            print(f"    No embeddings — skipping semantic clustering.")

    # Save clustering results
    cluster_file = STUDY_DIR / "dimensional_clusters.json"
    with open(cluster_file, "w") as f:
        json.dump(all_cluster_results, f, indent=2, ensure_ascii=False)
    print(f"\n  Dimensional clusters saved to {cluster_file}")

    if all_semantic_results:
        semantic_file = STUDY_DIR / "semantic_clusters.json"
        with open(semantic_file, "w") as f:
            json.dump(all_semantic_results, f, indent=2, ensure_ascii=False)
        print(f"  Semantic clusters saved to {semantic_file}")

    # Statistical comparisons
    if len(model_names) > 1:
        print(f"\n  Running pairwise statistical comparisons...")
        # Load summaries
        summaries = {}
        for mn in model_names:
            sf = STUDY_DIR / mn / "summary.json"
            if sf.exists():
                with open(sf) as f:
                    summaries[mn] = json.load(f)

        if len(summaries) > 1:
            comparisons = pairwise_comparisons(summaries)

            comp_file = STUDY_DIR / "pairwise_comparisons.json"
            with open(comp_file, "w") as f:
                json.dump(comparisons, f, indent=2, ensure_ascii=False)
            print(f"  Pairwise comparisons saved to {comp_file}")

            # Print significant results
            print(f"\n  Significant differences (Bonferroni p < 0.05):")
            any_sig = False
            for pair, dims in comparisons.items():
                for dim, stats in dims.items():
                    if isinstance(stats, dict) and stats.get("significant"):
                        any_sig = True
                        d = stats["cohens_d"]
                        print(f"    {pair} | {dim}: d={d:+.2f}, p={stats['p_bonferroni']:.4f}")
            if not any_sig:
                print(f"    (none)")

    # Temperature sweep analysis (if data exists)
    for mn in model_names:
        sweep_judged = load_judged(mn, tag="temperature_sweep")
        if sweep_judged:
            print(f"\n  Temperature sweep analysis: {mn}")
            sweep_results = analyze_temperature_sweep(mn, probes)
            if sweep_results:
                sweep_file = STUDY_DIR / mn / "temperature_sweep" / "analysis.json"
                with open(sweep_file, "w") as f:
                    json.dump(sweep_results, f, indent=2, ensure_ascii=False)
                print(f"    Saved to {sweep_file}")

    # Attractor diversity ranking
    print(f"\n  Attractor Diversity Ranking:")
    rankings = []
    for mn, clusters in all_cluster_results.items():
        overall = clusters.get("_all", {})
        km = overall.get("kmeans", {})
        db = overall.get("dbscan", {})
        display = MODEL_REGISTRY.get(mn, {}).get("display_name", mn)
        rankings.append({
            "model": mn,
            "display_name": display,
            "kmeans_k": km.get("best_k", 0),
            "dbscan_clusters": db.get("n_clusters", 0),
            "kmeans_entropy": km.get("entropy", 0),
            "dbscan_entropy": db.get("entropy", 0),
            "dominant_pct": km.get("dominant_cluster_pct", 100),
        })

    # Sort by entropy (higher = more diverse)
    rankings.sort(key=lambda r: r["kmeans_entropy"], reverse=True)
    for i, r in enumerate(rankings, 1):
        print(f"    {i}. {r['display_name']:25s} "
              f"k={r['kmeans_k']} clusters, "
              f"entropy={r['kmeans_entropy']:.2f}, "
              f"dominant={r['dominant_pct']:.0f}%")

    # Save rankings
    rankings_file = STUDY_DIR / "attractor_rankings.json"
    with open(rankings_file, "w") as f:
        json.dump(rankings, f, indent=2, ensure_ascii=False)

    print(f"\n  Analysis complete.")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Attractor Archaeology Study — Analysis Pipeline"
    )
    parser.add_argument("models", nargs="*", help="Models to analyze")
    parser.add_argument("--all", action="store_true",
                        help="Analyze all models with judged data")
    parser.add_argument("--probes", default="core",
                        help="Probe set (same as runner)")
    args = parser.parse_args()

    from model_personalities_study.core_values.probes import get_probes
    probes = get_probes(args.probes)

    if args.all:
        model_names = []
        for d in sorted(STUDY_DIR.iterdir()):
            if d.is_dir() and (d / "judged.json").exists():
                model_names.append(d.name)
    else:
        model_names = args.models

    if not model_names:
        print("No models specified. Use --all or provide model names.")
        parser.print_help()
        return

    print(f"Analyzing: {', '.join(model_names)}")
    run_full_analysis(model_names, probes)


if __name__ == "__main__":
    main()
