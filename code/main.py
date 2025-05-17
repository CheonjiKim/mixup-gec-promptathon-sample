import os
import pandas as pd
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split

from code.config import ExperimentConfig
from code.prompts.templates import TEMPLATES
from code.utils.experiment import ExperimentRunner

def main():
    load_dotenv()
    api_key = os.getenv('UPSTAGE_API_KEY')
    if not api_key:
        raise ValueError("API key not found in environment variables")
    
    # 템플릿 고정: 'best'
    template_name = 'best'
    config = ExperimentConfig(
        template_name=template_name,
        temperature=0.01,
        batch_size=5,
        experiment_name=f"eval_{template_name}"
    )

    # 데이터 로드
    train = pd.read_csv(os.path.join(config.data_dir, 'train.csv'))
    test = pd.read_csv(os.path.join(config.data_dir, 'test.csv'))

    # 토이 데이터 사용
    toy_data = train.sample(n=config.toy_size, random_state=config.random_seed).reset_index(drop=True)

    # train/valid 분할
    train_data, valid_data = train_test_split(
        toy_data,
        test_size=config.test_size,
        random_state=config.random_seed
    )

    # 실험 실행
    runner = ExperimentRunner(config, api_key)
    result = runner.run_template_experiment(train_data, valid_data)

    recall = result['valid_recall']['recall']
    precision = result['valid_recall']['precision']

    print(f"\n✅ 템플릿 '{template_name}' 평가 결과:")
    print(f"Recall: {recall:.2f}%")
    print(f"Precision: {precision:.2f}%")

    # 테스트 데이터 예측
    print("\n=== 테스트 데이터 예측 시작 ===")
    final_config = ExperimentConfig(
        template_name=template_name,
        temperature=0.0,
        batch_size=5,
        experiment_name="final_submission"
    )
    final_runner = ExperimentRunner(final_config, api_key)
    test_results = final_runner.run(test)

    output = pd.DataFrame({
        'id': test['id'],
        'cor_sentence': test_results['cor_sentence']
    })
    output.to_csv("submission_baseline.csv", index=False)

    print("\n📦 제출 파일 생성 완료: submission_baseline.csv")
    print(f"사용된 템플릿: {template_name}")
    print(f"예측된 샘플 수: {len(output)}")


if __name__ == "__main__":
    main()
