# 🧪 MixUp_푸바오 : Grammar Error Correction Promptathon 

본 레포지토리는 Grammar Error Correction Promptathon  실험을 재현하고 확장하기 위한 코드 및 가이드를 제공합니다.

## 📌 프로젝트 개요

* **목표**: ex. Solar Pro API를 활용하여 프롬프트 만으로 한국어 맞춤법 교정 성능을 개선한다. 
* **접근 전략**:
  * 두 가지 종류의 scoring 방식으로 출력 문장을 평가한다.
    <br>
    
   <img src="https://github.com/user-attachments/assets/a49d3b10-865c-4bc8-916c-da3660513bc2" width=70% />
   
  * **Method 1**: `Similarity`, `Fluency`, `Typo` 기반으로, 두 개의 `candidate output`을 비교한다.
  * **Method 2**: 모델 API 를 호출하여 두 개의 `candidate output`을 비교한다.
    <br>
    
  
* **주요 실험 내용**:
  * 영어 `system prompt`와 한국어 `system prompt` 비교 평가
  * `Role`, `Instructions`, `Example`을 모두 제공한 `system prompt`
  * `Role`, `Example`을 모두 제공한 `system prompt`
  * `Example`의 개수를 달리하며 만든 `system prompt`
  * 멀티턴 실험
  * 두 개의 서로 다른 프롬프트(1. 원본과 에러 유형 아웃풋 출력, 2. 원본 수정)
  * `step-by-step` instruction  
  
    
---

## ⚙️ 환경 세팅 & 실행 방법

### 1. 사전 준비 

```bash
git clone https://github.com/CheonjiKim/mixup-gec-promptathon-sample.git
cd your-repo/experiment
```

### 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 실험 실행

```bash
python run_experiment.py --input sample_input.txt --output result.json
```

> 📎 실행 옵션 (예시):
> `--input`: 실험 대상 파일
> `--output`: 결과 저장 파일 경로

---


## 🚧 실험의 한계 및 향후 개선

* **한계**:
  
  * Ground Truth가 올바르지 않은 문장인 경우, 학습 데이터에 대해 과대 적합 발생 가능성이 있음 (Ground truth 문장의 구두점의 비일관성, 구어체와 문어체의 혼용)
  * 일부 문장에 대해서 여전히 맞춤법이 틀리는 경우가 존재한다. (예, `싫어 <-> 실어`, `역할을 하다 <-> 역수를 하다` 등)
  
* **향후 개선 방향**:

  * 배치(batch) 연산 적용 → 빠른 교정을 위해 한 번의 query에 여러 개의 문장을 입력하고, 여러 개의 교정 문장을 받기
  * 최고 성능을 내는 프롬프트 나열 찾기(예, 띄어쓰기 규칙 instruction, 맞춤법 규칙 instruction 중 어느 것을 윗쪽에 둘 것인지)
  * 최상의 멀티턴 프롬프트 찾기 -> 전문가 에이전트를 다양화하여 정확한 교정 문장 얻어내기 (예, 맞춤법 위주의 전문가, 띄어쓰기 위주의 전문가, 도메인 특화 코퍼스 전문가 등으로 분화)
  * 다양한 교정 상황을 반영하는 예시 조합 찾기

---

## 📂 폴더 구조

```
.
├── README.md
├── code
│   ├── __init__.py
│   ├── __pycache__
│   ├── config.py
│   ├── main.py
│   ├── prompts
│   ├── requirements.txt
│   └── utils
├── data
│   ├── sample_submission.csv
│   ├── test.csv
│   └── train.csv
├── eda.ipynb
├── final_prompt.py
├── mixup-gec-promptathon-sample
│   ├── README.md
│   └── prompt_template_sample.json
├── prompt_template_sample.json
└── submission_cutter.ipynb
```
