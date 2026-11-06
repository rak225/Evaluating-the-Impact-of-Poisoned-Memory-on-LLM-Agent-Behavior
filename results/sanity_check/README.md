# Sanity check for eval_metrics.py

- run_p100_k1.csv: copy of the real baseline memory-poisoning log (llama3.2:3b, 1 task). Not a grid result, just used to test parsing.
- run_p0_k1.csv: hand-edited copy with Attack Successful set to 1, used ONLY to confirm the script flags a contaminated clean control. Not an experimental result.
- smoke_test_output.txt: script parses the real log correctly.
- warning_test_output.txt: script warns when clean-control ASR > 0, as intended.
