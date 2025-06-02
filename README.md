
# Chess Engine Project Roadmap

## Phase 1: Core Engine (Data & Rules Model)
1. **Native Python Engine (Naive Implementation)**:
   - Use simple 8×8 array representation.
   - Implement move generation via regular loops (for each square, check piece type, generate moves).
   - Handle special moves (castling, en passant, promotions) with conditional logic.
2. **Python Bitboard Engine**:
   - Rework the representation to use 64-bit bitboards for each piece type.
   - Replace loop-based move generation with bitwise operations, sliding attackers via precomputed tables or simple ray-tracing.
   - Ensure full legality checks (checks, pins, etc.) using bitboard masking.
3. **Rust Engine**:
   - Port the Python bitboard engine logic into Rust for performance.
   - Use Rust's safety and speed to optimize move generation, evaluation, and search.
   - Provide Python bindings or a CLI for integration/testing.

- **Game State Checks**: For each engine iteration, include check, checkmate, stalemate, threefold repetition, fifty-move rule.

---

## Phase 2: Classical AI (Search-Based Model)
- **Evaluation Function**: Material + piece-square tables + simple positional features.
- **Minimax + α–β**: Depth-limited search with pruning; quiescence search for captures.

---

## Phase 3: Neural Evaluation (Learned Static Evaluator)
- **Data Sourcing**:
  - Public master games (TWIC, Lichess PGN) and/or self-play games from Phase 2 engine.
  - Sample positions at fixed ply intervals; label with final outcome and/or engine centipawn scores.
- **Preprocessing**: Encode positions as tensor planes (bitboards for each piece, side to move, castling rights, etc.).
- **Model**: Small MLP or CNN in PyTorch to predict evaluation (win/draw/loss or centipawn score).
- **Integration**: Swap neural evaluator into the α–β search in place of handcrafted eval.

---

## Phase 3A: Training Options for Neural Evaluator
- **Local RTX 3070 GPU**:
  1. **Setup**: Install CUDA-compatible PyTorch; verify with `torch.cuda.is_available()`.
  2. **Prototype & Iterate Locally**: Train on subsets (50k–200k positions) to tune hyperparameters.
  3. **Scale Considerations**: Full master-game corpus (millions of samples) may take many hours per epoch on a 3070. Consider AWS instances when training time becomes excessive.
- **AWS SageMaker Training Job**:
  1. **Prepare `train.py`**: Accept hyperparameters via `argparse`, load data from S3 or generate via self-play, save final `model.pth` to `/opt/ml/model`.
  2. **Use SageMaker PyTorch Estimator**:
     ```python
     from sagemaker.pytorch import PyTorch
     estimator = PyTorch(
         entry_point="train.py",
         role="arn:aws:iam::<account-id>:role/SageMakerExecRole",
         framework_version="1.12",
         py_version="py38",
         instance_count=1,
         instance_type="ml.p3.2xlarge",
         hyperparameters={"epochs": 10, "batch_size": 256, "learning_rate": 1e-3},
     )
     estimator.fit({"training": "s3://<bucket>/chess-data/train/"})
     ```
  3. **Result**: SageMaker manages GPUs, logs to CloudWatch, and saves trained model to S3.

---

## Phase 3B: Inference / Deployment Options
- **Initial Low-Traffic Deployment (Lambda + API Gateway)**:
  - **Advantages**:
    - Pay-per-invoke; minimal cost when idle.
    - Scales automatically from 0 to N concurrent calls.
  - **Packaging**:
    - Bundle inference script (`lambda_function.py`) and `model.pth` (under 512 MB `/tmp`) into a deployment package or container image.
    - Ensure total unzipped size < 10 GB; use Lambda Layers if needed.
  - **Cold-Start Mitigation**:
    - Keep package minimal (only PyTorch/TorchScript and model file).
    - Use Lambda provisioned concurrency if latency is critical.
  - **CORS**: Configure API Gateway to allow `Access-Control-Allow-Origin: https://yourdomain.com`.
- **Switching to SageMaker Endpoint When Traffic Grows**:
  1. **Upload Model to S3**: `model.tar.gz` containing `inference.py` and `model.pth`.
  2. **Create SageMaker Model**:
     ```python
     from sagemaker.pytorch import PyTorchModel
     pytorch_model = PyTorchModel(
         model_data="s3://<bucket>/evaluator/model.tar.gz",
         role="arn:aws:iam::<account-id>:role/SageMakerExecutionRole",
         framework_version="1.12.1",
         py_version="py38",
         entry_point="inference.py",
         source_dir="."
     )
     endpoint = pytorch_model.deploy(
         initial_instance_count=1,
         instance_type="ml.m5.large",
         endpoint_name="chess-evaluator-endpoint"
     )
     ```
  3. **Endpoint Behavior**:
     - Always-on instance; pay hourly for instance.
     - Provides stable HTTPS URL; handle SigV4 or front with API Gateway for simpler auth.
  4. **Front-End Switching**:
     - Update Netlify proxy (`netlify.toml`) to redirect `/api/evaluate` from Lambda → SageMaker endpoint URL.
     - Minimal code changes; traffic shifts seamlessly.
- **Alternative Inference Path (ECS/Fargate or EC2)**:
  - Dockerize a Flask/FastAPI server that loads `model.pth` at startup.
  - Deploy container to ECS/Fargate behind an Application Load Balancer.
  - Use AWS ECR to store image; configure ALB with HTTPS and CORS headers.
- **Elastic Inference & SageMaker Neo**:
  - For GPU acceleration at lower cost, attach an EI accelerator (eia2.medium) to a SageMaker endpoint.
  - Optionally compile model with SageMaker Neo for optimized binary to reduce inference latency.

---

## Phase 4: AlphaZero-Style (Policy+Value MCTS)
- **Network Architecture**: Residual CNN or simplified policy+value heads.
- **MCTS Loop**:
  1. Self-play with MCTS guided by the network (PUCT selection, no rollouts).
  2. Collect (position, MCTS visit-distribution, game outcome) tuples.
  3. Retrain the network on that data.
  4. Iterate.
- **Infrastructure**: Batched network inference, parallel self-play, checkpointing, arena evaluation.

---

## Analysis & Move-Quality Evaluation
- **Raw Evaluation**: Both Phase 2 and 3/4 engines expose a numeric evaluation (centipawns or win-probability).
- **Blunder/Mistake Detection**:
  1. **Eval Before**: Query engine’s score prior to move.
  2. **Best Move**: Generate engine’s top move and its score.
  3. **Played Move**: Score the user’s move result.
  4. **Δ**: Compute score drop (absolute centipawns or win-prob swing).
  5. **Thresholds**:
     - Inaccuracy: Δ ≥ 50 cp (or 10% win-prob swing).
     - Mistake: Δ ≥ 100 cp (or 20% swing).
     - Blunder: Δ ≥ 200 cp (or 30% swing).
  6. **Labels**: Tag moves as inaccuracy, mistake, or blunder accordingly.
- **UI Integration**: Present tagged feedback in CLI/web UI alongside move suggestions and evaluations.

---

## UX & Integration
- **CLI**: Play vs. engine, perft tests, PGN import/export, evaluation/blunder reports.
- **Web UI**: (Optional) React-based board display, move highlighting, analysis panel. Easily host via Netlify with API calls to AWS Lambda or SageMaker.
- **Testing**: Perft regression, special-move tests, evaluation consistency, and move-quality annotation checks.

---

*Each phase builds on the last: Phase 1 ensures correctness; Phase 2 provides a search baseline and data labels; Phase 3 replaces rules with learned evaluation; Phase 4 fully automates learning. Deployment starts serverless on Lambda/API Gateway and can seamlessly transition to SageMaker or ECS as traffic grows.*
