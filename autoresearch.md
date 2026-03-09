# Autoresearch: Falsifying Functionalism

This document tracks our autonomous machine learning experiments to prove the "Form Follows Fitness" (FFF) framework.

## The Ultimate Goal
The architectural dogma "form follows function" (Sullivan, Le Corbusier) is an untested, degenerated special case. Our project uses machine learning to empirically prove that a design object's geometry is almost entirely predictable from its **material constraints**, **geography**, and **era**—rather than its function. 

By maximizing the F1 score of predicting Style and Nation from purely geometric and material properties, we demonstrate that the fitness landscape maps heavily to these pressures, leaving function as a mere constant.

## Plan & Progress
- [x] Create sandbox directory `chair_autoresearch/` to prevent editing original articles directly.
- [x] Extract the classification task into `train_eval.py` that outputs a single metric (`FINAL_SCORE`).
- [x] Create an infinite loop in `agent.py` to query **Gemini 2.5 Pro** to mutate the code and evaluate the result.
- [x] Update the agent's prompt to align strictly with proving the FFF thesis.
- [x] **Generalization Pipeline**: Created `data_gathering_pipeline/fetch_digitaltmuseum.py` to pull metadata for other consumer goods (ceramics, tables, lamps) to prove the theory generalizes beyond chairs.
- [ ] Run the autonomous loop.

## The Agent Loop (`agent.py`)
1. Reads `train_eval.py`.
2. Sends the code to Gemini 2.5 Pro with explicit instructions to maximize the F1 score and optimize the ML architecture.
3. Gemini writes a mutated Python file.
4. The agent executes the new file.
5. If the `FINAL_SCORE` goes up, it saves the file as the new baseline and writes "keep" to `results.tsv`.
6. If the score goes down or the script crashes, it reverts the file.
7. Repeats indefinitely.

## Integrating Other Museum Databases
To prove the FFF theory holds universally, we have added a separate data gathering pipeline:
- `data_gathering_pipeline/fetch_digitaltmuseum.py`
This script connects to the DigitaltMuseum / KulturNav open API. It searches for specific object categories (like "keramikk" or "bord"), builds a metadata database, and formats the material and geometric feature CSVs.
Once you run this pipeline, it outputs offline datasets (e.g., `data_keramikk/`). You can then simply update the `data_dir` variable in `chair_autoresearch/train_eval.py` to point to `../data_keramikk/`, and the agent will instantly begin optimizing the theoretical framework against this new domain.

## Execution
Ensure your API key is set, then run:
```powershell
cd chair_autoresearch
python agent.py
```
Leave it running overnight to find the most optimal mathematical mapping of the fitness landscape.
*Last updated: 2026-03-09*