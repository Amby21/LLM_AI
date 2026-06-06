from ragas import evaluate
from ragas.metrics import(faithfulness, answer_relevancy, context_precision)
from datasets import Dataset
from agent import run_agent, last_run

TEST_SET = [
    {
        "question":     "What encryption is required for PII?",
        "ground_truth": "PII must be encrypted using AES-256"
    },
    {
        "question":     "How many days to delete GDPR data?",
        "ground_truth": "30 days"
    },
    {
        "question":     "What is Loss Ratio?",
        "ground_truth": "Claims paid divided by premiums earned"
    }
]

def run_ragas_evaluation():
    """For each test question:
     1. Run agent → collects question, contexts, answer
      2. Feed into RAGAS
      3. Get score """
    
    questions = []
    answers = []
    context_lists = []
    ground_truths = []

    for test in TEST_SET:
        print(f"\nRunning:{test['question']}")

        answer = run_agent(test['question'])
        questions.append(last_run["question"])
        answers.append(last_run["answer"])
        context_lists.append(last_run["contexts"])
        ground_truths.append(test["ground_truth"])
        print(f"Answer:   {answer[:80]}...")
        print(f"Contexts: {len(last_run['contexts'])} retrieved")

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": context_lists,
        "ground_truth": ground_truths
    })

    print("\nRunning RAGAS evaluation...")
    scores = evaluate(
        dataset,
        metrics=[
            faithfulness,      # answer grounded in context?
            answer_relevancy,  # answer addresses question?
            context_precision  # retrieved chunks relevant?
        ]
    )


    # Print results
    print("\n" + "="*40)
    print("RAGAS SCORES")
    print("="*40)
    print(f"Faithfulness:      {scores['faithfulness']:.2f}")
    print(f"Answer Relevancy:  {scores['answer_relevancy']:.2f}")
    print(f"Context Precision: {scores['context_precision']:.2f}")
    print("="*40)

    # Suggestions
    print("\nSUGGESTIONS:")
    if scores["faithfulness"] < 0.8:
        print("  ⚠️  Low faithfulness:")
        print("     LLM answering beyond retrieved context")
        print("     Fix: stricter system prompt")

    if scores["context_precision"] < 0.7:
        print("  ⚠️  Low context precision:")
        print("     Wrong chunks being retrieved")
        print("     Fix: raise threshold or smaller chunks")

    if scores["answer_relevancy"] < 0.8:
        print("  ⚠️  Low answer relevancy:")
        print("     Answer not addressing the question")
        print("     Fix: improve system prompt")

    return scores


if __name__ == "__main__":
    run_ragas_evaluation()
