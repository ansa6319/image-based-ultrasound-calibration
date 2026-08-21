import torch
from scipy.io import loadmat, savemat
import utilities as su
from beamformer import calibration_beamformer

# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ============================================================
# LOAD FILES
# ============================================================

NUM_TRIOS = 20

STAGE1_FILE = DATA_DIR / "cal_150frames_fracdisp_002_divtrans.mat"
STAGE2_FILE = DATA_DIR / "cal_150frames_fracdisp_005_divtrans.mat"
OUTPUT_FILE = RESULTS_DIR / "result_cal_two_stage.mat"

# ============================================================
# OPTIMIZE
# ============================================================
# Run Stage 1 optimization
stage1_model = calibration_beamformer(torch.zeros(6), stage1_data, (46, 54), NUM_TRIOS)
stage1_last, _, stage1_loss = su.optimize(stage1_model, lr=5.0, patience=30, max_iters=300, name="Stage 1")
# Run Stage 2 optimization (optional)
stage2_model = calibration_beamformer(stage1_last, stage2_data, (11, 19), NUM_TRIOS)
_, stage2_best, stage2_loss = su.optimize(stage2_model, lr=5.0, patience=30, max_iters=300, name="Stage 2")

# ============================================================
# CALIBRATION MATRICES
# ============================================================
stage1_X = su.calibration_matrix(stage1_last).detach().numpy()
stage2_X = su.calibration_matrix(stage2_best).detach().numpy()

# ============================================================
# SAVE OUTPUT
# ============================================================
savemat(OUTPUT_FILE, {
    "stage1_last_calib": stage1_last.numpy(),
    "stage1_loss": stage1_loss,
    "stage1_X": stage1_X,
    "stage2_final_calib": stage2_best.numpy(),
    "stage2_loss": stage2_loss,
    "stage2_X": stage2_X,
    "num_trios": NUM_TRIOS,
})
print(f"Saved: {OUTPUT_FILE}")
