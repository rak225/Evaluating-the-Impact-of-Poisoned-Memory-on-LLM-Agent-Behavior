import json
import os
import random
import re
import shutil
from pathlib import Path
import httpx2

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings


SEED = 42
TARGET_MEMORY_COUNT = 100

POISON_RATES = [0.00, 0.10, 0.25, 0.50, 0.75, 1.00]

SOURCE_DB = Path(
    "memory_db/direct_prompt_injection/combined_attack_gpt-4o-mini"
)

OUTPUT_ROOT = Path(
    "memory_db/controlled_poison_rate_sweep"
)


def extract_field(text, start_marker, end_marker):
    start = text.find(start_marker)
    if start == -1:
        return None

    start += len(start_marker)

    end = text.find(end_marker, start)
    if end == -1:
        return None

    return text[start:end].strip()


def extract_attacker_tool(text):
    match = re.search(
        r'by using the "([^"]+)" tool',
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return None


def extract_tools(text):
    marker = "Tools: "
    pos = text.find(marker)

    if pos == -1:
        return []

    raw = text[pos + len(marker):].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def build_clean_version(poisoned_text):
    agent = extract_field(
        poisoned_text,
        "Agent: ",
        "; Task:"
    )

    task = extract_field(
        poisoned_text,
        "Task: ",
        "\n Answer:"
    )

    if task is None:
        task = extract_field(
            poisoned_text,
            "Task: ",
            "; Workflow:"
        )

    attacker_tool = extract_attacker_tool(poisoned_text)

    tools = extract_tools(poisoned_text)

    normal_tools = []

    for tool in tools:
        name = (
            tool.get("function", {})
            .get("name")
        )

        if not name:
            continue

        if attacker_tool and name == attacker_tool:
            continue

        normal_tools.append(tool)

    if not agent or not task or not normal_tools:
        return None

    normal_tool_name = (
        normal_tools[0]["function"]["name"]
    )

    clean_workflow = [
        {
            "message": (
                f"Complete the legitimate task: {task}"
            ),
            "tool_use": [normal_tool_name]
        }
    ]

    return (
        f"Agent: {agent}; "
        f"Task: {task}; "
        f"Workflow: {clean_workflow}; "
        f"Tools: {json.dumps(normal_tools)}"
    )


def main():
    random.seed(SEED)

    embeddings = OpenAIEmbeddings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        http_client=httpx2.Client(
            headers={"Accept-Encoding": "identity"}
        )
    )

    source_db = Chroma(
        persist_directory=str(SOURCE_DB),
        embedding_function=embeddings
    )

    source = source_db.get()

    pairs = []

    for i, poisoned_text in enumerate(
        source["documents"]
    ):
        if not poisoned_text:
            continue

        clean_text = build_clean_version(
            poisoned_text
        )

        if clean_text is None:
            continue

        pairs.append({
            "source_id": (
                source["ids"][i]
                if i < len(source["ids"])
                else str(i)
            ),
            "clean": clean_text,
            "poisoned": poisoned_text
        })

    print(
        f"Usable clean/poison pairs: {len(pairs)}"
    )

    if len(pairs) < TARGET_MEMORY_COUNT:
        raise RuntimeError(
            f"Need {TARGET_MEMORY_COUNT} pairs, "
            f"but only found {len(pairs)}."
        )

    #
    # Select ONE fixed set of 100 underlying
    # memories for every experimental condition.
    #
    rng = random.Random(SEED)

    selected_pairs = rng.sample(
        pairs,
        TARGET_MEMORY_COUNT
    )

    #
    # Fixed ordering makes conditions nested:
    # 10% poisons the first 10,
    # 25% poisons the first 25, etc.
    #
    poison_order = list(
        range(TARGET_MEMORY_COUNT)
    )

    rng.shuffle(poison_order)

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True
    )

    manifest = {
        "seed": SEED,
        "target_memory_count": (
            TARGET_MEMORY_COUNT
        ),
        "source_database": str(SOURCE_DB),
        "label_method": (
            "paired provenance-based synthetic "
            "clean controls"
        ),
        "conditions": []
    }

    for poison_rate in POISON_RATES:
        poison_count = round(
            TARGET_MEMORY_COUNT
            * poison_rate
        )

        poisoned_indices = set(
            poison_order[:poison_count]
        )

        rate_percent = int(
            poison_rate * 100
        )

        output_dir = (
            OUTPUT_ROOT
            / f"rate_{rate_percent}"
        )

        if output_dir.exists():
            shutil.rmtree(output_dir)

        db = Chroma(
            persist_directory=str(output_dir),
            embedding_function=embeddings
        )

        docs = []

        for i, pair in enumerate(
            selected_pairs
        ):
            poisoned = (
                i in poisoned_indices
            )

            text = (
                pair["poisoned"]
                if poisoned
                else pair["clean"]
            )

            metadata = {
                "poisoned": poisoned,
                "poison_rate": poison_rate,
                "source_id": pair["source_id"],
                "pair_index": i
            }

            docs.append(
                Document(
                    page_content=text,
                    metadata=metadata
                )
            )

        db.add_documents(docs)

        actual_poison = sum(
            1
            for doc in docs
            if doc.metadata["poisoned"]
        )

        actual_clean = (
            len(docs) - actual_poison
        )

        print(
            f"Created rate_{rate_percent}: "
            f"{actual_clean} clean, "
            f"{actual_poison} poisoned"
        )

        manifest["conditions"].append({
            "poison_rate": poison_rate,
            "poison_percent": rate_percent,
            "total_memories": len(docs),
            "clean_memories": actual_clean,
            "poisoned_memories": actual_poison,
            "database": str(output_dir)
        })

    manifest_file = (
        OUTPUT_ROOT / "manifest.json"
    )

    with open(
        manifest_file,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            manifest,
            f,
            indent=2
        )

    print()
    print(
        f"Manifest: {manifest_file}"
    )


if __name__ == "__main__":
    main()