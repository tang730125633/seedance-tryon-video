#!/usr/bin/env bash
set -euo pipefail

# Cloud GPU setup for virtual try-on / outfit swap experiments.
# Target: AutoDL Ubuntu + NVIDIA GPU.

export DEBIAN_FRONTEND=noninteractive

WORKDIR="${WORKDIR:-/root/autodl-tmp/work}"
COMFY_DIR="${COMFY_DIR:-$WORKDIR/ComfyUI}"

echo "== GPU =="
nvidia-smi || true

echo "== System packages =="
apt-get update
apt-get install -y \
  git git-lfs curl wget aria2 ffmpeg \
  python3 python3-venv python3-dev build-essential \
  libgl1 libglib2.0-0 libsm6 libxext6 libxrender1
git lfs install || true

mkdir -p "$WORKDIR"

if [ ! -d "$COMFY_DIR/.git" ]; then
  echo "== Clone ComfyUI =="
  git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFY_DIR"
fi

cd "$COMFY_DIR"

echo "== Python venv =="
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip wheel setuptools

echo "== PyTorch CUDA 12.8 =="
python -m pip install --index-url https://download.pytorch.org/whl/cu128 torch torchvision torchaudio

echo "== ComfyUI requirements =="
python -m pip install -r requirements.txt

mkdir -p custom_nodes models/checkpoints models/vae models/clip models/loras models/controlnet models/ultralytics models/sams

echo "== Custom nodes =="
clone_or_pull() {
  local repo="$1"
  local dir="$2"
  if [ -d "$dir/.git" ]; then
    git -C "$dir" pull --ff-only || true
  else
    git clone "$repo" "$dir"
  fi
  if [ -f "$dir/requirements.txt" ]; then
    python -m pip install -r "$dir/requirements.txt" || true
  fi
  if [ -f "$dir/install.py" ]; then
    python "$dir/install.py" || true
  fi
}

clone_or_pull https://github.com/ltdrdata/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager
clone_or_pull https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git custom_nodes/ComfyUI-VideoHelperSuite
clone_or_pull https://github.com/pzc163/Comfyui-CatVTON.git custom_nodes/Comfyui-CatVTON
clone_or_pull https://github.com/TemryL/ComfyUI-IDM-VTON.git custom_nodes/ComfyUI-IDM-VTON
clone_or_pull https://github.com/kijai/ComfyUI-segment-anything-2.git custom_nodes/ComfyUI-segment-anything-2

echo "== Smoke test imports =="
python - <<'PY'
import torch
print("torch", torch.__version__)
print("cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
PY

cat > "$COMFY_DIR/start_comfy_cloud.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd /root/autodl-tmp/work/ComfyUI
source .venv/bin/activate
python main.py --listen 0.0.0.0 --port 8188
SH
chmod +x "$COMFY_DIR/start_comfy_cloud.sh"

echo
echo "Done."
echo "Start ComfyUI with:"
echo "  $COMFY_DIR/start_comfy_cloud.sh"
echo
echo "Open port 8188 from AutoDL, or create an SSH tunnel:"
echo "  ssh -L 18188:127.0.0.1:8188 root@<host> -p <port>"
