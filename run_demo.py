"""
End-to-end demo:
1. Ingest 2 calls for Deal Acme -> show the brief evolving call over call
   (within-deal memory)
2. Ingest 1 call for a brand-new Deal Globex -> show the brief already
   surfacing tactics learned from Acme (cross-deal memory via the playbook bank)
"""
from src.agent import ingest_call, prep_next_call


def read_transcript(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def section(title: str):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    # --- Deal Acme: within-deal memory story ---
    section("BEFORE CALL 1 - Deal Acme (no memory yet)")
    print(prep_next_call("acme", "Acme"))

    section("Ingesting Acme call 1...")
    facts1 = ingest_call("acme", "Acme", 1, read_transcript("data/transcripts/acme_call1.txt"))
    print(f"Extracted: {facts1}")

    section("BEFORE CALL 2 - Deal Acme (memory from call 1)")
    print(prep_next_call("acme", "Acme"))

    section("Ingesting Acme call 2...")
    facts2 = ingest_call("acme", "Acme", 2, read_transcript("data/transcripts/acme_call2.txt"))
    print(f"Extracted: {facts2}")

    section("BEFORE CALL 3 - Deal Acme (memory from calls 1 + 2)")
    print(prep_next_call("acme", "Acme"))

    # --- Deal Globex: cross-deal memory story ---
    section("Ingesting Globex call 1 (brand new deal)...")
    facts3 = ingest_call("globex", "Globex", 1, read_transcript("data/transcripts/globex_call1.txt"))
    print(f"Extracted: {facts3}")

    section("BEFORE CALL 2 - Deal Globex (should surface Acme's annual-discount tactic)")
    print(prep_next_call("globex", "Globex"))


if __name__ == "__main__":
    main()
    # close the Hindsight client cleanly to avoid the "Unclosed client session"
    # aiohttp warning at the end of the run
    from src.config import get_hindsight
    get_hindsight().close()
