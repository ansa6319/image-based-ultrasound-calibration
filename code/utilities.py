import torch


def hilbert(x):
    n = x.shape[0]
    h = torch.zeros(n, dtype=x.dtype, device=x.device)
    if n % 2 == 0:
        h[0] = h[n // 2] = 1
        h[1:n // 2] = 2
    else:
        h[0] = 1
        h[1:(n + 1) // 2] = 2
    return torch.fft.ifft(torch.fft.fft(x, dim=0) * h.view(-1, *([1] * (x.ndim - 1))), dim=0)


def tracking_matrices(tracking):
    measurements = tracking[0][0][0]
    transforms = torch.empty((len(measurements), 4, 4), dtype=torch.float32)

    for i, m in enumerate(measurements):
        q0, qx, qy, qz = [float(m[k][0, 0]) for k in ("q0", "qx", "qy", "qz")]
        tx, ty, tz = [float(m[k][0, 0]) / 1000 for k in ("tx", "ty", "tz")]
        transforms[i] = torch.tensor([
            [q0*q0 + qx*qx - qy*qy - qz*qz, 2*(qx*qy - qz*q0), 2*(qx*qz + qy*q0), tx],
            [2*(qx*qy + qz*q0), q0*q0 - qx*qx + qy*qy - qz*qz, 2*(qy*qz - qx*q0), ty],
            [2*(qx*qz - qy*q0), 2*(qy*qz + qx*q0), q0*q0 - qx*qx - qy*qy + qz*qz, tz],
            [0, 0, 0, 1],
        ], dtype=torch.float32)

    return transforms


def calibration_matrix(calibration):
    rx, ry, rz = torch.deg2rad(calibration[:3])
    cx, sx = torch.cos(rx), torch.sin(rx)
    cy, sy = torch.cos(ry), torch.sin(ry)
    cz, sz = torch.cos(rz), torch.sin(rz)

    Rx = torch.eye(4, dtype=calibration.dtype, device=calibration.device)
    Ry = torch.eye(4, dtype=calibration.dtype, device=calibration.device)
    Rz = torch.eye(4, dtype=calibration.dtype, device=calibration.device)
    T = torch.eye(4, dtype=calibration.dtype, device=calibration.device)

    Rx[1, 1], Rx[1, 2], Rx[2, 1], Rx[2, 2] = cx, -sx, sx, cx
    Ry[0, 0], Ry[0, 2], Ry[2, 0], Ry[2, 2] = cy, sy, -sy, cy
    Rz[0, 0], Rz[0, 1], Rz[1, 0], Rz[1, 1] = cz, -sz, sz, cz
    T[:3, 3] = calibration[3:] / 1000

    return Rz @ Rx @ Ry @ T


def linear_interp(x, y, x_new):
    y = y.squeeze()
    idx = torch.searchsorted(x, x_new).clamp(1, x.numel() - 1)
    x0, x1 = x[idx - 1], x[idx]
    y0, y1 = y[idx - 1], y[idx]
    return y0 + (y1 - y0) * (x_new - x0) / (x1 - x0)



def corr2d_loss(a, b, eps=1e-12):
    a, b = a - a.mean(), b - b.mean()
    return 1 - torch.sum(a * b) / (torch.sqrt(torch.sum(a**2) * torch.sum(b**2)) + eps)


def optimize(model, lr, patience, max_iters, threshold=1e-4, name=""):
    optimizer = torch.optim.Adam([model.calibration], lr=lr)
    best_loss, best_calibration, no_improve, history = float("inf"), model.calibration.detach().clone(), 0, []

    for iteration in range(max_iters):
        optimizer.zero_grad()
        loss = model()
        value = float(loss.detach().item())
        current = model.calibration.detach().clone()
        history.append(value)

        if best_loss - value > threshold:
            best_loss, best_calibration, no_improve = value, current, 0
        else:
            no_improve += 1

        loss.backward()
        optimizer.step()

        if iteration % 10 == 0:
            print(f"{name}: iteration {iteration:03d}, loss = {value:.6f}")
        if no_improve >= patience:
            break

    return model.calibration.detach().clone(), best_calibration, torch.tensor(history).numpy()
