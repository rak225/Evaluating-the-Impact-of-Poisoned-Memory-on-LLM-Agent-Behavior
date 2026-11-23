import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results/sri_poison_rate_by_k.csv")

plt.figure(figsize=(8, 5))

for k in sorted(df["retrieval_k"].unique()):
    subset = df[df["retrieval_k"] == k]

    plt.plot(
        subset["poison_rate"],
        subset["poisoned_retrieval_fraction"],
        marker="o",
        label=f"k={k}"
    )

plt.xlabel("Poisoning Rate (%)")
plt.ylabel("Poisoned Retrieval Fraction")
plt.title("Poisoned-Memory Retrieval Across Poisoning Rates and Retrieval Depths")

plt.ylim(0, 1.05)
plt.grid(True)
plt.legend(title="Retrieval Depth")

plt.tight_layout()

plt.savefig(
    "results/sri_poison_rate_by_k.png",
    dpi=300
)

print("Wrote: results/sri_poison_rate_by_k.png")

