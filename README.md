# DermaVision DL 🔬

Medical image classification for skin lesion detection using deep learning.

> Built with PyTorch · FastAPI · React · MLflow · Docker

---

## 📋 Project Overview

Multi-class classification of skin lesions using the **HAM10000** dataset (10,000 dermatoscopic images across 7 lesion categories).

- **Model:** EfficientNet-B3 fine-tuned on ImageNet
- **Metrics:** AUC-ROC, Sensitivity, Specificity, F1-Score
- **Interface:** React + TypeScript frontend
- **Backend:** FastAPI with JWT authentication

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & docker-compose

### Setup

```bash
# Clone the repo
git clone https://github.com/Mohamedbd99/dermavision-dl.git
cd dermavision-dl

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run with Docker
```bash
docker-compose up --build
```
- API: http://localhost:8000
- Frontend: http://localhost:3000
- MLflow UI: http://localhost:5000

### Run tests
```bash
pytest tests/
```

---

## 📁 Project Structure

```
dermavision-dl/
├── src/
│   ├── data/           # Dataset & preprocessing
│   ├── models/         # Architecture & training
│   ├── api/            # FastAPI backend
│   └── utils/          # Config & metrics
├── frontend/           # React + TypeScript
├── notebooks/          # EDA, training, evaluation
├── tests/              # Unit & integration tests
├── docker/             # Dockerfiles
└── docker-compose.yml
```

---

## ⚠️ Ethical Considerations

This model is a **research prototype only** and is not intended for clinical use. The HAM10000 dataset has known demographic biases (predominantly European skin tones) which may affect performance across diverse populations. Class imbalance in the dataset is handled via weighted loss but users should interpret predictions with caution.

Dataset license: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)
