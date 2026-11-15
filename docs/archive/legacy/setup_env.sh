#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="mechinterp"
PYTHON_VERSION="3.10"

echo "=== 1. Prüfe Conda-Installation ==="
if ! command -v conda &>/dev/null; then
    for candidate in "$HOME/miniconda3/bin/conda" "$HOME/anaconda3/bin/conda" "$HOME/miniforge3/bin/conda" "/opt/conda/bin/conda"; do
        if [ -x "$candidate" ]; then
            eval "$("$candidate" shell.bash hook)"
            break
        fi
    done
fi

if ! command -v conda &>/dev/null; then
    echo "Conda wurde nicht gefunden. Installiere Miniconda nach $HOME/miniconda3 ..."
    INSTALLER="/tmp/Miniconda3-latest-Linux-x86_64.sh"
    curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o "$INSTALLER"
    bash "$INSTALLER" -b -u -p "$HOME/miniconda3"
    rm -f "$INSTALLER"
    eval "$("$HOME/miniconda3/bin/conda" shell.bash hook)"
    "$HOME/miniconda3/bin/conda" init bash
else
    eval "$(conda shell.bash hook)"
fi

conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main 2>/dev/null || true
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r 2>/dev/null || true

echo "=== 2. Erstelle / Aktiviere Conda-Umgebung '$ENV_NAME' (Python $PYTHON_VERSION) ==="
if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
    echo "Umgebung '$ENV_NAME' existiert bereits."
else
    conda create -y -n "$ENV_NAME" python="$PYTHON_VERSION"
fi

conda activate "$ENV_NAME"

echo "=== 3. Installiere PyTorch mit CUDA-Unterstützung (Blackwell sm_120 kompatibel) ==="
pip install --upgrade pip
pip install torch torchvision torchaudio

echo "=== 4. Installiere Mechanistic-Interpretability-Pakete ==="
# transformer_lens==2.18.0 und sae-lens==6.54.9 sind kompatibel mit klassischem HookedTransformer
pip install "transformer_lens==2.18.0" "sae-lens==6.54.9" "transformers<5.0" jupyterlab matplotlib pandas einops circuitsvis

echo "=== 5. System-Check (CUDA & GPU) ==="
python - <<'EOF'
import sys
import torch

print(f"Python-Version: {sys.version.split()[0]}")
print(f"PyTorch-Version: {torch.__version__}")
cuda_ok = torch.cuda.is_available()
print(f"CUDA verfügbar (torch.cuda.is_available()): {cuda_ok}")

if cuda_ok:
    device_count = torch.cuda.device_count()
    print(f"Anzahl GPUs: {device_count}")
    for idx in range(device_count):
        print(f"GPU {idx}: {torch.cuda.get_device_name(idx)}")
else:
    print("WARNUNG: Keine CUDA-fähige GPU erkannt!")
    sys.exit(1)
EOF
