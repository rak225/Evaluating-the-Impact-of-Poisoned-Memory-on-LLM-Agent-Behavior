import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(
    "results/sri_poison_rate_k5_repeated_with_exposure.csv"
)

plt.figure(figsize=(7, 4.5))

plt.plot(
    df["poison_rate"],
    df["poisoned_retrieval_fraction"],
    marker="o",
    label="Poisoned retrieval fraction",
)

plt.plot(
    df["poison_rate"],
    df["poison_exposure_rate"],
    marker="s",
    label="Poison-exposed case rate",
)

plt.xlabel("Poisoning Rate (%)")
plt.ylabel("Fraction")
plt.title("Effect of Poisoning Rate on Memory Exposure at k=5")

plt.ylim(0, 1.05)
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig(
    "results/sri_poison_rate_k5_repeated_exposure.png",
    dpi=300,
)

print(
    "Wrote: "
    "results/sri_poison_rate_k5_repeated_exposure.png"
)
