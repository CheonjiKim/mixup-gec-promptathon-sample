import os
import time
import pandas as pd
from tqdm import tqdm
from typing import Dict
import requests
import difflib
import re

from code.config import ExperimentConfig
from code.prompts.templates import TEMPLATES
from code.utils.metrics import evaluate_correction


class ExperimentRunner:
    def __init__(self, config: ExperimentConfig, api_key: str):
        self.config = config
        self.api_key = api_key
        self.template = TEMPLATES[config.template_name]
        self.api_url = config.api_url
        self.model = config.model

    def _make_prompt(self, text: str) -> Dict:
        prompts = TEMPLATES[self.config.template_name]
        return {
            "system": prompts["system_prompt"],
            "user": prompts["user_prompt"].format(text=text)
        }

    def _extract_input_text(self, prompt_text: str) -> str:
        match = re.search(r"입력:\s*(.*?)\s*출력:", prompt_text, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _similarity(self, a: str, b: str) -> float:
        return difflib.SequenceMatcher(None, a, b).ratio()

    def _fluency_score(self, sentence: str) -> float:
        score = 0.0
        sentence = sentence.strip()

        # 종결 표현 체크
        if re.search(r'(다|요|죠|네|군|지)[.!?]$', sentence):
            score += 1.5
        elif re.search(r'(다|요|죠|네|군|지)$', sentence):
            score += 1.0
        else:
            score -= 0.5

        if sentence.endswith(('.', '?', '!', '...')):
            score += 0.5
        else:
            score -= 0.5

        # 반복 단어 감점
        repeated = len(re.findall(r'\b(\w+)\s+\1\b', sentence))
        score -= 0.3 * repeated

        return score

    def _typo_count(self, sentence: str) -> int:
        return sum(1 for word in sentence.split() if not re.match(r"^[가-힣a-zA-Z0-9,.!?~]+$", word))

    def _score_candidate(self, output: str, original_input: str) -> float:
        sim_score = self._similarity(output, original_input)
        fluency = self._fluency_score(output)
        typos = self._typo_count(output)

        return (0.6 * sim_score) + (0.4 * fluency / 3) - (0.05 * typos)

    def _choose_best_via_llm(self, candidate1: str, candidate2: str, original_input: str) -> str:
        compare_prompt = {
            "system": "다음 두 문장 중 한국어 맞춤법, 띄어쓰기, 문법이 더 정확한 문장을 선택하세요. 의미는 유지되어야 합니다. 더 나은 문장만 그대로 출력하세요.",
            "user": f"""입력 문장: {original_input}

                {candidate1}
                {candidate2}

                더 적절한 문장을 한 줄로 출력하세요."""
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": compare_prompt["system"]},
                {"role": "user", "content": compare_prompt["user"]}
            ]
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[비교 API 실패] {e}")
            return candidate1

    def _call_api_single(self, prompts: Dict) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        candidates = []
        for _ in range(2):
            data = {
                "model": self.model,
                "temperature": self.config.temperature,
                "messages": [
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ]
            }
            try:
                response = requests.post(self.api_url, headers=headers, json=data)
                response.raise_for_status()
                raw_content = response.json()["choices"][0]["message"]["content"]
                output = raw_content.strip().split('\n')[0]
                candidates.append(output)
            except Exception as e:
                print(f"[API 실패] {e}")
            time.sleep(0.3)

        original_input = self._extract_input_text(prompts["user"])

        if not candidates:
            return ""
        elif len(candidates) == 1 or candidates[0] == candidates[1]:
            return candidates[0]
        else:
            return self._choose_best_via_llm(candidates[0], candidates[1], original_input)

    def run(self, data: pd.DataFrame) -> pd.DataFrame:
        results = []
        for _, row in tqdm(data.iterrows(), total=len(data)):
            prompt = self._make_prompt(row['err_sentence'])
            corrected = self._call_api_single(prompt)
            results.append({
                'id': row['id'],
                'cor_sentence': corrected
            })
        return pd.DataFrame(results)

    def run_template_experiment(self, train_data: pd.DataFrame, valid_data: pd.DataFrame) -> Dict:
        print(f"\n=== {self.config.template_name} 템플릿 실험 ===")

        print("\n[학습 데이터 실험]")
        train_results = self.run(train_data)
        train_recall = evaluate_correction(train_data, train_results)

        # 결과 정리 및 저장
        merged = train_data.copy().reset_index(drop=True)
        train_results = train_results.reset_index(drop=True)
        merged['predicted'] = train_results['cor_sentence']

        wrong = merged[merged['cor_sentence'] != merged['predicted']]
        wrong = wrong[['err_sentence', 'cor_sentence', 'predicted']]
        wrong.columns = ['input', 'ground_truth', 'predicted']
        wrong.to_csv("wrong_train_predictions2.csv", index=False, encoding='utf-8-sig')
        print(f"\n📄 틀린 예측 결과 저장 완료: wrong_train_predictions2.csv")

        print("\n[검증 데이터 실험]")
        valid_results = self.run(valid_data)
        valid_recall = evaluate_correction(valid_data, valid_results)

        return {
            'train_recall': train_recall,
            'valid_recall': valid_recall,
            'train_results': train_results,
            'valid_results': valid_results
        }
