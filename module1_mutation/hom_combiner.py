"""Higher-order mutant (HOM) combiner.

Combines two first-order mutants of the SAME function into one second-order
mutant, capped at max_hom_per_function combinations per function. Combination
is done at the text level: compute the changed region of mutant B relative to
the original function, and re-apply that exact textual change on top of
mutant A's mutated source. If B's original region is no longer present
verbatim in A's output (the two mutations overlap), the pair is skipped.
Every produced mutant is ast.parse-validated; failures are skipped and logged.
"""
from __future__ import annotations

import ast
import difflib
import itertools
import sys


def _changed_region(original: str, mutated: str) -> tuple[str, str] | None:
    """Return (orig_snippet, new_snippet) covering all line-level changes."""
    a, b = original.splitlines(keepends=True), mutated.splitlines(keepends=True)
    ops = [op for op in difflib.SequenceMatcher(a=a, b=b).get_opcodes()
           if op[0] != "equal"]
    if not ops:
        return None
    i1, i2 = ops[0][1], ops[-1][2]
    j1, j2 = ops[0][3], ops[-1][4]
    return "".join(a[i1:i2]), "".join(b[j1:j2])


def combine_pair(original: str, mutated_a: str, mutated_b: str) -> str | None:
    region = _changed_region(original, mutated_b)
    if region is None:
        return None
    orig_snip, new_snip = region
    if orig_snip == "" or orig_snip not in mutated_a:
        return None  # overlapping or ambiguous — skip
    if mutated_a.count(orig_snip) != 1:
        return None
    combined = mutated_a.replace(orig_snip, new_snip, 1)
    if combined.strip() in (original.strip(), mutated_a.strip(), mutated_b.strip()):
        return None  # degenerate: collapsed back to a first-order mutant
    return combined


def generate_homs(first_order: list[dict], max_per_function: int = 3,
                  log=print) -> list[dict]:
    """first_order: list of schema mutants (any class). Returns raw HOM dicts:
    {function, file, line, original_code, mutated_code, parents:[id,id]}.
    Only same-function pairs are combined, per the design."""
    by_func: dict[tuple[str, str], list[dict]] = {}
    for m in first_order:
        by_func.setdefault((m["file"], m["function"]), []).append(m)

    homs: list[dict] = []
    for (file, func), muts in sorted(by_func.items()):
        count = 0
        for a, b in itertools.combinations(muts, 2):
            if count >= max_per_function:
                break
            combined = combine_pair(a["original_code"], a["mutated_code"],
                                    b["mutated_code"])
            if combined is None:
                continue
            try:
                ast.parse(combined)
            except SyntaxError:
                log(f"[hom] {a['mutant_id']}+{b['mutant_id']} fails to parse, "
                    "skipped", file=sys.stderr)
                continue
            homs.append({
                "file": file, "function": func, "line": a["line"],
                "original_code": a["original_code"], "mutated_code": combined,
                "parents": [a["mutant_id"], b["mutant_id"]],
                "parent_operators": [a["mutation_operator"], b["mutation_operator"]],
                "parent_descriptions": [a["mutation_description"],
                                        b["mutation_description"]],
            })
            count += 1
    return homs
