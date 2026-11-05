
from retrieval_experiments.retrieval_depth import (
    retrieve_workflows,
    save_retrieval_log,
)


# Mock Chroma document for testing
class MockDocument:
    def __init__(self, memory_id, workflow, poisoned=False):
        self.page_content = (
            f"Task: sample; Workflow: [{workflow}];"
        )
        self.metadata = {
            "id": memory_id,
            "is_poisoned": poisoned,
        }


# Mock vector database
class MockVectorStore:
    def __init__(self):
        self.data = [
            (MockDocument("m1", "'check'", False), 0.1),
            (MockDocument("m2", "'verify'", False), 0.2),
            (MockDocument("m3", "'unsafe'", True), 0.3),
            (MockDocument("m4", "'finish'", False), 0.4),
        ]

    def similarity_search_with_score(self, query, k=4):
        return self.data[:k]


def test_retrieval():
    store = MockVectorStore()

    for k in [1, 3, 5, 10]:
        instruction, records, top_memory_content = retrieve_workflows(
            vectorstore=store,
            query="sample task",
            k=k,
        )

        expected_count = min(k, 4)

        assert len(records) == expected_count
        assert instruction is not None

        # Verify retrieved ranks
        assert [r["rank"] for r in records] == list(
            range(1, expected_count + 1)
        )

        # Verify multi-memory formatting
        if k == 1:
            assert "previous workflow" in instruction.lower()
        else:
            assert "Previous workflow 1:" in instruction

        output = save_retrieval_log(
            records=records,
            k=k,
            path=f"logs/retrieval/sanity_k{k}.json",
        )

        expected_poisoned = 0 if k == 1 else 1

        assert output["retrieved_count"] == expected_count
        assert output["poisoned_count"] == expected_poisoned
        assert output["poison_exposed"] == (expected_poisoned > 0)

        print(
            f"PASS: k={k}, "
            f"retrieved={expected_count}, "
            f"poisoned={expected_poisoned}"
        )

    print("\nAll retrieval sanity checks passed!")


if __name__ == "__main__":
    test_retrieval()
