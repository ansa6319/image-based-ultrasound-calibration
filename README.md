# Image-Based Ultrasound Calibration

This repository provides a minimal implementation of the two-stage image-based spatial calibration method for tracked ultrasound.

The method estimates the rigid transformation between the tracked tool coordinate system and the ultrasound image coordinate system by optimizing image similarity between tracked ultrasound frames.

## Repository Structure

```text
image-based-ultrasound-calibration/
│
├── README.md
├── LICENSE
├── requirements.txt
│
├── code/
│   ├── parent.py
│   ├── beamformer.py
│   └── utilities.py
│
├── data/
│   ├── README.md
│   ├── cal_150frames_fracdisp_002_divtrans.mat
│   └── cal_150frames_fracdisp_005_divtrans.mat
│
├── results/
│   └── result_cal_two_stage.mat
│

```

## Requirements

The demo requires Python 3 and the following packages:

- PyTorch
- NumPy
- SciPy

Install them with:

```bash
pip install torch numpy scipy
```


## Running the Demo

From the repository root, run:

```bash
python code/parent.py
```

The script loads the example datasets from the `data/` folder and saves the calibration results to the `results/` folder.

## Workflow

The implementation is divided into three small Python scripts.

### `parent.py`

This is the main script and the only file that needs to be executed.

It:

1. Loads the Stage 1 and Stage 2 calibration datasets.
2. Initializes the six calibration parameters:
   ```text
   [rx, ry, rz, tx, ty, tz]
   ```
3. Runs Stage 1 for robust initialization.
4. Uses the final Stage 1 estimate to initialize Stage 2.
5. Constructs the corresponding homogeneous calibration matrices.
6. Saves the calibration parameters, calibration matrices, and optimization loss histories.

The included example uses:

**Stage 1**
- Relative-translation-diversity trio selection
- 2% fractional displacement
- 46–54 mm axial ROI
- 20 trios

**Stage 2**
- Relative-translation-diversity trio selection
- 5% fractional displacement
- 11–19 mm axial ROI
- 20 trios

The optimization settings are defined directly in `parent.py`.

### `beamformer.py`

This file contains the differentiable ultrasound beamforming model.

During initialization it performs calculations that do not depend on the unknown calibration, including:

- acquisition-parameter extraction,
- beamforming-grid construction,
- tracked relative-motion calculation,
- center-frame beamforming.

During each forward pass it:

1. Constructs the current calibration matrix.
2. Transforms the common beamforming grid into the left- and right-frame coordinate systems.
3. Calculates transmit and receive propagation distances.
4. Calculates time of flight.
5. Interpolates the RF channel data.
6. Forms envelope images.
7. Computes the image-similarity loss between the center frame and the left/right frames.

### `utilities.py`

This file contains supporting functions used by the calibration workflow, including:

- tracked-pose conversion to homogeneous transformation matrices,
- calibration-matrix construction,
- linear RF interpolation,
- Hilbert transform,
- 2-D Pearson-correlation loss,
- optimization.

## Output

The calibration result is saved as:

```text
results/result_cal_two_stage.mat
```

The output contains:

- `stage1_last_calib` — Stage 1 calibration parameters
- `stage1_X` — Stage 1 homogeneous calibration matrix
- `stage1_loss` — Stage 1 optimization loss history
- `stage2_final_calib` — final Stage 2 calibration parameters
- `stage2_X` — final Stage 2 homogeneous calibration matrix
- `stage2_loss` — Stage 2 optimization loss history
- `num_trios` — number of trios used

The calibration parameter order is:

```text
[rx, ry, rz, tx, ty, tz]
```

Rotations are represented in degrees and translations in millimeters. The homogeneous calibration matrix is constructed using the rotation convention implemented in `utilities.py`, with translations converted to meters.

## Expected Optimization Behavior

Part (a) of the figure below shows the expected loss history for the two-stage calibration using the default settings.

Stage 1 typically produces the largest decrease in loss and provides the primary calibration update. Stage 2 is initialized from the Stage 1 result and uses frame trios with larger relative transducer displacement. Because these frames are more widely separated, their image similarity is lower, and the Stage 2 loss is therefore expected to remain at a higher value rather than reaching the lower loss values observed in Stage 1. For this reason, the absolute loss values from Stage 1 and Stage 2 should not be compared directly.

Stage 2 generally produces a smaller reduction in loss because the calibration has already been substantially improved by Stage 1. Nevertheless, this refinement can further improve the final geometric calibration. In the example provided here, the mean wire-line residual (MWLR) improved from 0.769 mm after Stage 1 to 0.341 mm after Stage 2.

Part (b) shows the corresponding N-wire validation, illustrating the positions of the reconstructed wire observations relative to the fitted wire lines for the Stage 1 and Stage 2 calibration results.

For applications where the Stage 1 accuracy is already sufficient, the second refinement stage may not be necessary. Stage 2 is intended as an optional refinement when higher calibration accuracy is desired.
<img width="3816" height="4136" alt="result" src="https://github.com/user-attachments/assets/3c7073cc-051e-4fe4-a279-cc853ac5cf56" />


## Adapting the Implementation to Another Dataset

The included data provide one reproducible example of the calibration workflow. To apply the method to another tracked ultrasound acquisition or transducer, replace the example input data with files containing the required acquisition geometry, RF channel data, and tracked tool poses.

See [`data/README.md`](data/README.md) for the required data structure, dimensions, coordinate conventions, and units.


## Citation

If you use this implementation, please cite the associated manuscript:

> Citation to be added upon publication.

## License

This project is distributed under the MIT License. See `LICENSE` for details.
