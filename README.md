# Chess Engine Project Roadmap

[![Build Status](https://github.com/vaishakkmenon/chess-bots/actions/workflows/ci.yml/badge.svg)](https://github.com/vaishakkmenon/chess-bots/actions/workflows/ci.yml)
(#)  
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](#)  
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](#)  
[![Rust](https://img.shields.io/badge/rust-1.60%2B-orange.svg)](#)  


A step-by-step blueprint for building a high-performance chess engine—from a native Python implementation all the way to a Rust-powered, neural-enhanced AlphaZero-style system.

---

## 📖 Table of Contents

1. [🚀 About](#about)  
2. [🌟 Features](#features)  
3. [📦 Installation](#installation)  
4. [🚀 Usage](#usage)  
5. [🗺️ Roadmap](#roadmap)  
   - [Phase 1: Core Engine (Data & Rules Model)](#phase-1-core-engine-data--rules-model)  
   - [Phase 2: Classical AI (Search-Based Model)](#phase-2-classical-ai-search-based-model)  
   - [Phase 3: Neural Evaluation (Learned Static Evaluator)](#phase-3-neural-evaluation-learned-static-evaluator)  
     - [Phase 3A: Training Options](#phase-3a-training-options-for-neural-evaluator)  
     - [Phase 3B: Inference & Deployment](#phase-3b-inference--deployment-options)  
   - [Phase 4: AlphaZero-Style (Policy + Value MCTS)](#phase-4-alphazero-style-policy--value-mcts)  
6. [🛠️ Contributing](#contributing)  
7. [📜 License](#license)  
8. [🙏 Acknowledgments](#acknowledgments)  

---

## 🚀 About

Modern chess engines blend algorithmic rigor with data-driven insights. This repository outlines a **progressive roadmap**—from a basic Python engine that uses simple loops and an 8×8 array, to a **Rust** implementation leveraging bitboards and a neural evaluator trained on grandmaster games. The final goal is an AlphaZero-inspired, self-learning Monte Carlo Tree Search engine.

All phases build on the last:  
1. Phase 1 ensures correctness with rule-based logic.  
2. Phase 2 provides a search baseline via Minimax with α–β pruning.  
3. Phase 3 replaces handcrafted evaluation with a neural network.  
4. Phase 4 fully automates learning via self-play and MCTS.  

_Content for this roadmap is derived from the existing project README._ fileciteturn1file0

---

## 🌟 Features

- 🔄 **Multiple Implementations**  
  - Native Python: clear, easy-to-understand code using an 8×8 array.  
  - Python Bitboards: faster move generation with bitwise masks and ray tracing.  
  - Rust Port: highly optimized engine for top-tier performance.  

- 🧠 **Search & Evaluation**  
  - Depth-limited Minimax with α–β pruning and quiescence search.  
  - Material and piece-square heuristic evaluation function.  
  - Optional neural evaluator (MLP or CNN) trained on master-level games.  

- 🤖 **Neural Network Integration**  
  - Custom PyTorch models predicting centipawn scores.  
  - Training pipelines for local RTX 3070 or AWS SageMaker.  
  - Seamless swap-in for rule-based evaluation during search.  

- 🔄 **AlphaZero-Style Self-Play**  
  - Residual CNN with policy and value heads.  
  - PUCT-based MCTS without rollouts.  
  - Automated data collection and iterative retraining.  

- 🌐 **Deployment Options**  
  - Serverless inference with AWS Lambda and API Gateway.  
  - Scalable SageMaker endpoints.  
  - Containerized Flask or FastAPI on ECS/Fargate or EC2.  

---

## 📦 Installation

**Prerequisites**  
- Python 3.8 or higher  
- Rust 1.60 or higher (for the Rust port and beyond)  
- (Optional) CUDA-enabled GPU for Phase 3 training  

1. **Clone the Repository**  
   - Obtain a local copy of this project by cloning the repository URL.  

2. **Set Up the Python Environment**  
   - Create and activate a virtual environment for Python.  
   - Install all required Python dependencies.  

3. **Build the Rust Port (Phase 1 Rust Only)**  
   - Navigate to the Rust subfolder and build the project in release mode.  

4. **Verify Dependencies**  
   - Confirm that PyTorch recognizes a CUDA-compatible GPU if planning to train the neural evaluator locally.  

---

## 🚀 Usage

### 🐍 Native Python Engine (Phase 1)

- **Run Tests**  
  - Execute the provided test suite to verify correct move generation and rule handling.  
  - Perft tests are available to validate move counts at various depths.  

- **Play vs. Engine (CLI)**  
  - Use the command-line interface to play against the engine with human input.  

- **Benchmarking**  
  - Perform perft-divide to break down move generation counts per initial move.  
  - Compare performance metrics for further optimization.  

### 🦀 Rust Engine (Phase 1–2)

- **Run Tests**  
  - Run all Rust-based unit tests to ensure bitboard logic and search functions behave correctly.  

- **CLI Integration**  
  - Invoke the compiled Rust binary to play games or run benchmarks.  

### 🧠 Neural Evaluator (Phase 3)

- **Data Preparation**  
  - Generate sample positions from master games and/or self-play games to serve as training data.  

- **Local Training (RTX 3070)**  
  - Train the neural evaluator on position datasets by specifying hyperparameters (number of epochs, batch size, learning rate).  
  - Monitor GPU utilization and training metrics.  

- **Swapping Evaluators**  
  - By default, the engine uses a handcrafted evaluation function.  
  - Replace the rule-based evaluator with the trained neural evaluator by specifying a model checkpoint.  

### ☁️ Inference & Deployment (Phase 3B)

- **Serverless (Lambda + API Gateway)**  
  - **Pros**:  
    - Cost-effective for low or sporadic traffic (pay per invocation).  
    - Automatic scaling from zero to many concurrent requests.  
  - **Deployment Steps**:  
    1. Package the inference script and model weights into a deployment artifact that meets AWS Lambda size constraints.  
    2. Create an AWS Lambda function with minimal dependencies and upload the deployment package.  
    3. Configure an API Gateway endpoint (e.g., `/evaluate`) and enable CORS.  
    4. Monitor cold-start latency and consider using Lambda Provisioned Concurrency if low-latency guarantees are required.  

- **SageMaker Endpoint**  
  1. Upload the trained model files to an S3 bucket.  
  2. Create a SageMaker model resource pointing to the S3 location and providing an inference script.  
  3. Deploy a real-time endpoint on an appropriate instance (e.g., ml.m5.large) under a chosen endpoint name.  
  4. Secure the endpoint via IAM or place an API Gateway in front for simpler authentication.  
  5. Update the front-end or proxy configuration (e.g., Netlify redirects) to send evaluation requests to the SageMaker endpoint.  

- **Containerized Hosting (ECS/Fargate or EC2)**  
  - **Containerization**:  
    - Build a Docker image that installs minimal dependencies (PyTorch, inference dependencies) and loads the model at startup.  
    - Push the image to a container registry (ECR).  
  - **Deployment**:  
    - Deploy the image to an ECS cluster using Fargate for serverless containers, or provision an EC2 instance behind an Application Load Balancer.  
    - Configure HTTPS and CORS on the load balancer so that front-end clients can securely call the inference service.  

- **Elastic Inference & SageMaker Neo**  
  - Attach an Elastic Inference accelerator (e.g., eia2.medium) to a SageMaker endpoint to reduce GPU costs for inference.  
  - Optionally compile the PyTorch model into an optimized binary using SageMaker Neo to reduce inference latency on both edge and cloud instances.  

---

## 🗺️ Roadmap

### Phase 1: Core Engine (Data & Rules Model) fileciteturn1file0

1. **Native Python Engine (Naïve Implementation)**  
   - **Representation**: Implement the board as an 8×8 two-dimensional array.  
   - **Move Generation**:  
     - Iterate over each square, detect the piece type, and generate legal moves according to chess rules.  
     - Handle special cases such as castling, en passant, and promotions.  
   - **Game State Checks**:  
     - Detect checks, checkmates, and stalemates.  
     - Implement threefold repetition detection and fifty-move rule counting.  

2. **Python Bitboard Engine**  
   - **Representation**: Use 64-bit integer bitboards to represent piece occupancy.  
   - **Move Generation**:  
     - Replace nested loops with bitwise operations for knight and king moves.  
     - For sliding pieces (rook, bishop, queen), initially use simple ray tracing per square.  
     - Integrate helper utilities like least-significant-bit extraction for iteration.  
   - **Legal-Check Integration**:  
     - Accurately detect pin scenarios and ensure moves do not leave the king in check.  

3. **Rust Engine**  
   - **Language Port**: Translate the Python bitboard logic into Rust, leveraging type safety and zero-cost abstractions.  
   - **Optimizations**:  
     - Use inline functions or macros for attack-mask computations.  
     - Employ Rust’s built-in bitwise operations and efficient memory handling.  
   - **Interoperability**:  
     - Optionally expose Python bindings via a tool like PyO3, or provide a standalone command-line binary.  

---

### Phase 2: Classical AI (Search-Based Model)

- **Evaluation Function**  
  - Start with material balance scoring (assign values to pieces).  
  - Introduce piece-square tables for positional weights.  
  - Add simple positional heuristics such as pawn structure and mobility.  

- **Minimax with α–β Pruning**  
  - Implement a depth-limited depth-first search that prunes unpromising branches.  
  - Add a quiescence search subroutine to handle capture-only extensions and reduce horizon effect.  
  - Incorporate basic move ordering improvements (prioritize captures and checks) and late move reductions.  

- **Perft Testing**  
  - Provide three levels of perft:  
    - **Basic Perft**: total node count at a given depth.  
    - **Perft-Divide**: breakdown by initial move.  
    - **Hashed Perft**: use a transposition table to cache visited positions for performance benchmarking.  

---

### Phase 3: Neural Evaluation (Learned Static Evaluator)

1. **Data Sourcing**  
   - Gather publicly available master game records (e.g., TWIC or Lichess PGN dumps).  
   - Optionally generate additional positions via self-play using the Phase 2 engine.  
   - Sample positions at fixed ply intervals, labeling them with final game outcomes or engine centipawn scores.  

2. **Preprocessing**  
   - Convert each position into a set of input planes:  
     - Bitboard planes (one plane per piece type for both.colors).  
     - Auxiliary planes for castling rights, side to move, and en passant square.  

3. **Model Architecture**  
   - **Option A: MLP (Fully Connected)**  
     - Flatten the board representation and feed through multiple dense layers.  
   - **Option B: CNN (Convolutional Neural Network)**  
     - Treat the 8×8 grid as a 2D input, applying convolutional layers to capture spatial patterns.  
   - Configure output to predict either a continuous centipawn score or a ternary win/draw/loss classification.  

4. **Integration with Search**  
   - Allow toggling between the handcrafted evaluator and the neural model through a configuration flag.  
   - When the neural evaluator is active, call the model to score leaf positions during Minimax search.  

---

#### Phase 3A: Training Options for Neural Evaluator

- **Local RTX 3070 GPU**  
  1. **Setup**  
     - Install a CUDA-compatible version of PyTorch and verify GPU availability.  
  2. **Prototype & Iterate**  
     - Train on a small dataset (e.g., 50,000 to 200,000 positions) to tune hyperparameters such as learning rate and batch size.  
  3. **Scale Considerations**  
     - For training on the full master-game corpus (millions of positions), plan for multi-day training runs; consider renting cloud GPU instances if local resources become a bottleneck.  

- **AWS SageMaker Training Job**  
  1. **Prepare Training Script**  
     - Accept hyperparameters (number of epochs, batch size, learning rate) via command-line arguments.  
     - Load data directly from S3 or generate on the fly through self-play.  
     - Save the final model to the designated output location.  
  2. **Configure SageMaker Estimator**  
     - Use a PyTorch estimator specifying the entry point, instance type (e.g., p3.2xlarge), and hyperparameters.  
  3. **Review Outcomes**  
     - SageMaker manages GPU provisioning, logging, and checkpointing to S3.  
     - Download the trained model from S3 for local inference or further training.  

---

#### Phase 3B: Inference & Deployment Options

- **Serverless with Lambda + API Gateway**  
  - **Pros**:  
    - Cost-effective for low or sporadic traffic (pay per invocation).  
    - Automatic scaling from zero to many concurrent requests.  
  - **Deployment Steps**:  
    1. Package the inference script and model weights into a deployment artifact that meets AWS Lambda size constraints.  
    2. Create an AWS Lambda function with minimal dependencies and upload the deployment package.  
    3. Configure an API Gateway endpoint (e.g., `/evaluate`) and enable CORS.  
    4. Monitor cold-start latency and consider using Lambda Provisioned Concurrency if low-latency guarantees are required.  

- **SageMaker Real-Time Endpoint**  
  1. Upload the trained model files to an S3 bucket.  
  2. Create a SageMaker model resource pointing to the S3 location and providing an inference script.  
  3. Deploy a real-time endpoint on an appropriate instance (e.g., ml.m5.large) under a chosen endpoint name.  
  4. Secure the endpoint via IAM or place an API Gateway in front for simpler authentication.  
  5. Update the front-end or proxy configuration (e.g., Netlify redirects) to send evaluation requests to the SageMaker endpoint.  

- **Containerized Hosting (ECS/Fargate or EC2)**  
  - **Containerization**:  
    - Build a Docker image that installs minimal dependencies (PyTorch, inference dependencies) and loads the model at startup.  
    - Push the image to a container registry (ECR).  
  - **Deployment**:  
    - Deploy the image to an ECS cluster using Fargate for serverless containers, or provision an EC2 instance behind an Application Load Balancer.  
    - Configure HTTPS and CORS on the load balancer so that front-end clients can securely call the inference service.  

- **Elastic Inference & SageMaker Neo**  
  - Attach an Elastic Inference accelerator (e.g., eia2.medium) to a SageMaker endpoint to reduce GPU costs for inference.  
  - Optionally compile the PyTorch model into an optimized binary using SageMaker Neo to reduce inference latency on both edge and cloud instances.  

---

### Phase 4: AlphaZero-Style (Policy + Value MCTS)

- **Network Architecture**  
  - Design a Residual CNN trunk followed by two output heads:  
    - **Policy Head**: Outputs a probability distribution over legal moves.  
    - **Value Head**: Outputs a scalar estimate of the position’s expected outcome.  
  - Input features include bitboard representations for each piece type, game metadata (castling rights, side to move), and minimal move history if desired.  

- **MCTS Loop**  
  1. **Self-Play**  
     - For each position, run MCTS with PUCT selection, expanding leaf nodes using the network’s policy and value estimates (no rollout-based evaluation).  
     - Collect training data as triplets: `(position, visit distribution over moves, game outcome)`.  
  2. **Training**  
     - Use the self-play data to minimize a combined loss: cross-entropy for policy and mean-squared error for value.  
     - Optionally add regularization terms and use data augmentation (random symmetries of the board).  
  3. **Iteration**  
     - Continuously cycle through self-play, dataset augmentation, and network retraining.  
     - Periodically run an arena evaluation where the current best network faces the previous best to validate genuine improvement.  

- **Infrastructure Considerations**  
  - **Batched Inference**: Aggregate multiple MCTS leaf evaluations into a single batch call to the network to maximize GPU utilization.  
  - **Parallel Self-Play**: Use multiple processes or multiple GPUs to generate self-play games concurrently.  
  - **Checkpointing & Versioning**: Save intermediate model checkpoints and track Elo ratings over generations.  

---

## 🛠️ Contributing

Contributions are welcome! To get started:

1. **Fork the Repository**  
2. **Create a Feature Branch**  
   - Use a descriptive branch name such as `feature/your-feature-name`.  
3. **Implement & Commit Changes**  
   - Follow the project’s coding conventions: adhere to PEP 8 for Python and rustfmt guidelines for Rust code.  
   - Clearly comment nontrivial logic, especially in bitboard and search modules.  
4. **Run Tests**  
   - For the Python engine, run the existing test suite under `tests/bitboard_tests`.  
   - For the Rust engine, run `cargo test` in the Rust subfolder.  
5. **Open a Pull Request**  
   - Describe your changes in detail and reference any related issues (e.g., “Closes #123”).  
   - Ensure continuous integration checks pass before requesting review.  

_For major improvements or significant refactoring, please open an issue first to discuss the proposed changes._

---

## 📜 License

This project is licensed under the **MIT License**. Refer to the `LICENSE` file in this repository for full details.

---

## 🙏 Acknowledgments

- **Awesome README Examples** by [Mati as Singers](https://github.com/matiassingers/awesome-readme) for styling inspiration.  
- **Chess Programming Wiki** for bitboard tutorials and attack-mask explanations.  
- **PyTorch** community for model-building resources.  
- **AWS Documentation** for deployment best practices.  

---

_With ❤️ and ♟️,  
Vaishak Menon_
