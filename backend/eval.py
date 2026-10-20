import sys
import time

from rag import ask, retrieve

# (question, expected section number, keywords in a correct answer; "a|b" = either one)
TESTS = [
    ("What is the 1.5X rule?", "8.0", ["1.5"]),
    ("When can I withdraw my company registration?", "11.0", ["24"]),
    ("How many red flags lead to debarment and for how long?", "10.0", ["three|3", "45"]),
    ("When does the Dream Company option open for a branch?", "8.1", ["60"]),
    ("What is the CTC limit of the first offer for the Dream Company option?", "8.1", ["15"]),
    ("Can a student who accepted a PPO sit for other companies?", "6.0", ["dream"]),
    ("Within how long must an off-campus offer be reported to the Placement cell?", "7.0", ["one day|1 day|a day|24 hours"]),
    ("What happens if a student skips selection after registering without a valid reason?", "5.3", ["warning"]),
    ("When does the placement process begin each year?", "5.0", ["april"]),
    ("How long before interviews must a company share the shortlist?", "5.6", ["1 hour|one hour|01 hour"]),
    ("Are cell phones allowed in a test?", "11.0", ["not allowed|no cell|prohibited|cannot|can't"]),
    ("On what basis are slots allotted to companies?", "5.5", ["package"]),
    ("How long is the B.Tech internship after the third year?", "9.0", ["45"]),
    ("How soon is a student's choice among multiple offers communicated to the company?", "5.7", ["24"]),
]

OUT_OF_SCOPE = [
    "Who is the Prime Minister of India?",
    "What is the hostel fee at MNIT Jaipur?",
]
REFUSAL = ["could not find", "couldn't find", "not found", "no information", "not mentioned"]


def has(answer, keys):
    return all(any(alt in answer for alt in k.lower().split("|")) for k in keys)


def main():
    with_answers = "--answers" in sys.argv
    hit1 = hit4 = ans_ok = 0

    for q, prefix, keys in TESTS:
        if with_answers:
            result = ask(q)
            hits, answer = result["sources"], result["answer"].lower()
            time.sleep(2)
        else:
            hits, answer = retrieve(q), ""
            time.sleep(0.5)

        flags = [h["section"].startswith(prefix + " ") for h in hits]
        h1, h4 = bool(flags and flags[0]), any(flags)
        hit1 += h1
        hit4 += h4
        print(f"{'PASS' if h4 else 'FAIL'} | top1={'Y' if h1 else 'N'} | {q}")
        if not h4:
            print("     got:", [h["section"][:30] for h in hits])
        if with_answers:
            ok = has(answer, keys)
            ans_ok += ok
            print(f"     answer {'PASS' if ok else 'FAIL'} (expected {keys})")

    n = len(TESTS)
    print(f"\nRetrieval: hit@1 = {hit1}/{n}, hit@4 = {hit4}/{n}")

    if with_answers:
        print(f"Answer keyword check: {ans_ok}/{n}")
        refused = 0
        for q in OUT_OF_SCOPE:
            answer = ask(q)["answer"].lower()
            time.sleep(2)
            ok = any(r in answer for r in REFUSAL)
            refused += ok
            print(f"{'PASS' if ok else 'FAIL'} | out-of-scope | {q}")
        print(f"Refusal check: {refused}/{len(OUT_OF_SCOPE)}")


if __name__ == "__main__":
    main()