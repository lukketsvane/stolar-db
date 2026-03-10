import os
import re
import subprocess
import time
import shutil

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Please install the Google GenAI SDK: pip install google-genai")
    exit(1)

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Please set the GEMINI_API_KEY environment variable.")
    print("Run this in PowerShell before executing:")
    print("$env:GEMINI_API_KEY=\"your_key_here\"")
    exit(1)

client = genai.Client(api_key=api_key)

# We use gemini-2.5-pro as it is excellent at coding tasks
model_name = 'gemini-2.5-pro'

def evaluate_code():
    result = subprocess.run(["python", "train_eval.py"], capture_output=True, text=True)
    if result.returncode != 0:
        return 0.0, result.stderr
    
    match = re.search(r"FINAL_SCORE:\s*([0-9.]+)", result.stdout)
    if match:
        return float(match.group(1)), result.stdout
    return 0.0, result.stdout

def get_new_code(current_code):
    system_msg = """You are an expert AI researcher working on a groundbreaking PhD project.
Your ultimate goal is to falsify the architectural dogma "form follows function" and replace it with the "Form Follows Fitness" (FFF) framework. 
To prove this, we are using machine learning to show that a design object's form (geometry) is highly predictable from its material constraints, geography, and era—far more than its function.

Your immediate task is to modify the provided Python code to maximize the FINAL_SCORE output (macro F1 score for predicting Style and Nation).
The code uses sklearn on geometric and material features extracted from museum databases.
You can experiment with:
- Different classifiers (RandomForest, ExtraTrees, HistGradientBoosting, SVC, MLP, etc.)
- Hyperparameter tuning
- Data scaling (StandardScaler, MinMaxScaler)
- Feature selection, engineering, PCA, or combination

CRITICAL: Output ONLY valid Python code inside a single ```python block. Do not provide explanations."""
    
    user_msg = f"Current code:\n```python\n{current_code}\n```\n\nPlease provide an improved version."
    
    response = client.models.generate_content(
        model=model_name,
        contents=system_msg + "\n\n" + user_msg,
        config=types.GenerateContentConfig(
            temperature=0.7,
        )
    )
    
    output = response.text
    # Extract code from markdown block
    match = re.search(r"```python\n(.*?)```", output, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: if no block, assume the whole output is code
    return output.replace("```python", "").replace("```", "").strip()

def main():
    print(f"Starting Autoresearch loop with Gemini API")
    print("Evaluating baseline...")
    best_score, _ = evaluate_code()
    print(f"Baseline Score: {best_score}")

    with open("results.tsv", "w") as f:
        f.write("iteration\tscore\tstatus\n")
        f.write(f"0\t{best_score}\tkeep (baseline)\n")

    # Run indefinitely to find the absolute best fitness landscape mapping
    i = 1
    while True:
        print(f"\n--- Iteration {i} ---")
        with open("train_eval.py", "r", encoding="utf-8") as f:
            current_code = f.read()
        
        print("Generating new code mutation with Gemini...")
        try:
            new_code = get_new_code(current_code)
        except Exception as e:
            print(f"API Error: {e}")
            time.sleep(5)
            continue
        
        # Save new code
        with open("train_eval.py", "w", encoding="utf-8") as f:
            f.write(new_code)
        
        print("Evaluating mutation...")
        score, output = evaluate_code()
        print(f"Mutation Score: {score}")
        
        if score > best_score:
            print(">>> IMPROVED! Keeping new code.")
            best_score = score
            with open("results.tsv", "a") as f:
                f.write(f"{i}\t{score}\tkeep\n")
            # Save a backup of the best
            shutil.copy("train_eval.py", f"train_eval_best_{i}.py")
        else:
            if score == 0.0:
                print(">>> CRASHED or Invalid Output. Reverting.")
            else:
                print(">>> WORSE. Reverting.")
            with open("train_eval.py", "w", encoding="utf-8") as f:
                f.write(current_code)
            with open("results.tsv", "a") as f:
                f.write(f"{i}\t{score}\tdiscard\n")
                
        # To avoid rate limits
        time.sleep(5)
        i += 1

if __name__ == "__main__":
    main()