import math
import string
from collections import Counter
from pathlib import Path

from nltk.probability import FreqDist

# resolve relative to this file, so it works no matter which directory the app is started from
_STOPWORDS_FILE = Path(__file__).resolve().parent / "stopwords.txt"
with open(_STOPWORDS_FILE, encoding="utf-8") as f:
    STOPWORDS = frozenset(line.strip() for line in f if line.strip())
PUNCT = set(string.punctuation)


class TextProcessor:
    """Stateless corpus-linguistic helpers. All methods work on lists of (lower-case) string tokens."""

    @staticmethod
    def clean_tokens(tokens, remove_stopwords=False, remove_punct=False):
        cleaned = []

        for token in tokens:
            if remove_punct and all(ch in string.punctuation for ch in token):
                continue
            if remove_stopwords and token.lower() in STOPWORDS:
                continue
            cleaned.append(token)
        return cleaned

    @staticmethod
    def concordance(tokens, target, width=5):
        """KWIC lines: (left context, match, right context) for every hit of `target`.
        `target` can be a single word or a phrase ("production licence"). Case-insensitive."""
        words = target.lower().split()
        if not words:
            return []
        n = len(words)
        lowered = [t.lower() for t in tokens]

        results = []
        for i in range(len(lowered) - n + 1):
            if lowered[i] == words[0] and lowered[i:i + n] == words:
                left = " ".join(tokens[max(0, i - width): i])
                match = " ".join(tokens[i: i + n])
                right = " ".join(tokens[i + n: i + n + width])
                results.append((left, match, right))

        return results

    @staticmethod
    def ngrams(tokens, target=None, n=3, position="any"):
        """All n-grams (as tuples) in `tokens`.

        If `target` is given, only n-grams containing it are returned:
        position="any"   -> target anywhere in the n-gram
        position="first" -> n-gram starts with target
        position="last"  -> n-gram ends with target
        """
        if n < 1 or len(tokens) < n:
            return []
        if position not in ("any", "first", "last"):
            raise ValueError("position must be 'any', 'first' or 'last'")

        target = target.lower() if target else None
        grams = []
        for i in range(len(tokens) - n + 1):
            gram = tuple(tokens[i: i + n])
            if target is not None:
                lowered = [t.lower() for t in gram]
                if position == "first" and lowered[0] != target:
                    continue
                if position == "last" and lowered[-1] != target:
                    continue
                if position == "any" and target not in lowered:
                    continue
            grams.append(gram)
        return grams

    @staticmethod
    def ngram_counts(tokens, target=None, n=3, position="any"):
        """Counter of how often each n-gram occurs (see `ngrams`)."""
        return Counter(TextProcessor.ngrams(tokens, target, n, position))

    @staticmethod
    def freq_dist(tokens):
        return FreqDist(tokens)

    @staticmethod
    def token_freq(tokens, target):
        """Raw frequency of `target` (tokens are expected to be lower case, as produced by Document)."""
        return tokens.count(target.lower())

    @staticmethod
    def collocates(token_lists, target, window=4, min_freq=2, measure="logdice", exclude_stopwords=True):
        """Words that occur near `target`, ranked by an association measure.

        token_lists: list of token lists, one per document (pass [tokens] for a single document).
                     Windows never run across document boundaries.
        window:      number of tokens on each side of the node word.
        measure:     "logdice" (default), "pmi" or "freq" - the column used for sorting.
        Returns a list of dicts: collocate, cooccurrence, collocate_freq, pmi, logdice.

        PMI     = log2( f(node,c) * N / (f(node) * f(c) * 2*window) )
        logDice = 14 + log2( 2 * f(node,c) / (f(node) + f(c)) )
        PMI favours rare words; logDice is more stable, and not affected by corpus size.
        """
        if measure not in ("logdice", "pmi", "freq"):
            raise ValueError("measure must be 'logdice', 'pmi' or 'freq'")
        target = target.lower().strip()
        if not target:
            return []

        pair_counts = Counter()
        word_counts = Counter()
        node_count = 0
        total = 0

        for tokens in token_lists:
            lowered = [t.lower() for t in tokens]
            word_counts.update(lowered)
            total += len(lowered)
            for i, token in enumerate(lowered):
                if token != target:
                    continue
                node_count += 1
                lo, hi = max(0, i - window), min(len(lowered), i + window + 1)
                for j in range(lo, hi):
                    if j != i:
                        pair_counts[lowered[j]] += 1

        if node_count == 0:
            return []

        rows = []
        for word, f_nc in pair_counts.items():
            if f_nc < min_freq:
                continue
            if exclude_stopwords and (word in STOPWORDS or all(ch in PUNCT for ch in word)):
                continue
            f_c = word_counts[word]
            pmi = math.log2(f_nc * total / (node_count * f_c * 2 * window))
            logdice = 14 + math.log2(2 * f_nc / (node_count + f_c))
            rows.append({
                "collocate": word,
                "cooccurrence": f_nc,
                "collocate_freq": f_c,
                "pmi": pmi,
                "logdice": logdice,
            })

        sort_key = {"logdice": "logdice", "pmi": "pmi", "freq": "cooccurrence"}[measure]
        rows.sort(key=lambda r: (-r[sort_key], r["collocate"]))
        return rows