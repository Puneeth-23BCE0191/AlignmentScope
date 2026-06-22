from worker import generate_reasoning
from monitor import analyze_chain
from scorer import get_icon, get_risk_icon, compute_alignment_score


def main():
    user_prompt = input("Enter Prompt: ")

    result = generate_reasoning(user_prompt)
    steps = result["steps"]
    answer = result["answer"]

    analysis = analyze_chain(steps)
    step_analyses = analysis["steps"]
    alignment_score = analysis["overall_alignment_score"]
    risk_level = analysis["overall_risk_level"]
    chain_summary = analysis["chain_summary"]

    print("\n" + "=" * 60)
    print("ALIGNMENT ANALYSIS")
    print("=" * 60)

    for i, (step, result_step) in enumerate(zip(steps, step_analyses), start=1):
        label = result_step["label"].upper()
        icon = get_icon(label)
        print(f"\nStep {i}")
        print(f"  Reasoning : {step}")
        print(f"  Label     : {icon} {label}")
        print(f"  Reason    : {result_step['reason']}")

    risk_icon = get_risk_icon(risk_level)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Alignment Score : {alignment_score}/100")
    print(f"  Risk Level      : {risk_icon} {risk_level}")
    print(f"  Chain Summary   : {chain_summary}")

    print("\n" + "=" * 60)
    print("FINAL ANSWER")
    print("=" * 60)
    print(answer)


if __name__ == "__main__":
    main()