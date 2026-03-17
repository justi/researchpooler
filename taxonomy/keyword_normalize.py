"""
Keyword post-processing normalization for classification pipeline.

Applies: lowercase, depluralization, single-word removal,
deduplication against existing keywords, and substring removal.
"""

import inflect

_engine = inflect.engine()

# Terms that are inherently plural or should not be depluralized
PLURAL_EXCEPTIONS = {
    "neural networks",
    "gaussian processes",
    "kernel methods",
    "markov chain monte carlo",
    "bayesian networks",
    "support vector machines",
    "random forests",
    "decision trees",
    "genetic algorithms",
    "hidden markov models",
    "graph neural networks",
    "generative adversarial networks",
    "recurrent neural networks",
    "convolutional neural networks",
    "large language models",
    "diffusion models",
    "generative models",
    "language models",
    "foundation models",
    "transformer models",
    "recommender systems",
    "multi-agent systems",
    "operating systems",
    "distributed systems",
    "control systems",
    "formal methods",
    "stochastic methods",
    "online algorithms",
    "data structures",
    "knowledge graphs",
    "graph embeddings",
}


def depluralize_word(word):
    """Depluralize a single word, handling edge cases for technical terms."""
    # Don't depluralize very short words
    if len(word) <= 2:
        return word

    singular = _engine.singular_noun(word)
    if singular and singular != word:
        return singular
    return word


def depluralize_keyword(keyword):
    """Depluralize a multi-word keyword by depluraling the last word.

    Technical convention: the head noun (last word) carries the plural.
    E.g., "neural networks" -> "neural network"
    """
    # Check if keyword is in the exceptions list (keep as-is)
    if keyword in PLURAL_EXCEPTIONS:
        return keyword

    words = keyword.split()
    if len(words) < 2:
        return keyword

    # Only depluralize the last word (head noun)
    last = depluralize_word(words[-1])
    return " ".join(words[:-1] + [last])


def normalize_keywords(keywords, existing_keywords=None):
    """Normalize a list of keywords from LLM output.

    Steps:
    1. Lowercase all keywords
    2. Depluralize (singular form, with exception list)
    3. Drop single-word keywords (< 2 space-separated words)
    4. Deduplicate against existing keywords if provided
    5. Remove substring keywords (if A is substring of B, keep only B)

    Args:
        keywords: list of keyword strings from LLM
        existing_keywords: set of existing keyword strings to dedup against

    Returns:
        list of normalized, unique keyword strings
    """
    if not keywords:
        return []

    existing_set = set(k.lower() for k in (existing_keywords or []))

    # Step 1: Lowercase
    normalized = [kw.strip().lower() for kw in keywords]

    # Step 2: Depluralize
    normalized = [depluralize_keyword(kw) for kw in normalized]

    # Step 3: Drop single-word keywords
    normalized = [kw for kw in normalized if len(kw.split()) >= 2]

    # Step 4: Deduplicate -- prefer existing form if exists
    deduped = []
    seen = set()
    for kw in normalized:
        if kw in seen:
            continue
        # Use existing form if it exists
        if kw in existing_set:
            deduped.append(kw)
        else:
            deduped.append(kw)
        seen.add(kw)

    # Step 5: Remove substring keywords (keep the longer/more specific one)
    result = []
    for kw in deduped:
        is_substring = False
        for other in deduped:
            if kw != other and kw in other:
                is_substring = True
                break
        if not is_substring:
            result.append(kw)

    return result
