import torch
import utilities as su


class calibration_beamformer(torch.nn.Module):
    """Differentiable calibration beamformer for saved left-center-right trios."""

    def __init__(self, calibration, data, roi_mm, num_trios=20):
        super().__init__()
        self.calibration = torch.nn.Parameter(calibration.detach().clone())

        # Acquisition parameters 
        acq = data[-1, 0]
        rx_pos = torch.as_tensor(acq["data"]["rx_pos"][0][0], dtype=torch.float32)   # [element, xyz], m
        tx_pos = torch.as_tensor(acq["data"]["tx_pos"][0][0], dtype=torch.float32)   # [element, xyz], m
        fs = torch.as_tensor(acq["data"]["fs"][0][0], dtype=torch.float32).squeeze()  
        t0 = torch.as_tensor(acq["data"]["t0"][0][0], dtype=torch.float32).squeeze()
        self.c = torch.as_tensor(acq["data"]["c"][0][0], dtype=torch.float32).squeeze() # m/s
        self.ele_focus = torch.as_tensor(acq["data"]["elevation_focus"][0][0], dtype=torch.float32).squeeze()
        tx_z = tx_pos[0, 2]
        dist_vector = torch.arange(data[0, 0][0].shape[0], dtype=torch.float32) / fs + t0 / fs

        # Beamforming parameters
        x = torch.linspace(-4e-3, 4e-3, 80)
        z = torch.linspace(roi_mm[0]*1e-3, roi_mm[1]*1e-3, 80)
        Z, X = torch.meshgrid(z, x, indexing="ij")
        grid = torch.stack((X, torch.zeros_like(X), Z, torch.ones_like(X))).reshape(4, -1)
        shape = Z.shape
        

        # Calibration-independent tracking transforms and center-frame beamforming
        trios = []
        for sweep in range(data.shape[1]):
            rf_cal = data[0, sweep][0]
            T = su.tracking_matrices(data[-1, sweep]["data"]["trackingcal"])
            T_inv = torch.linalg.inv(T)

            for left in range(0, rf_cal.shape[3] - 2, 3):
                center, right = left + 1, left + 2
                A_left_inv = T_inv[left] @ T[center]
                A_right_inv = T_inv[right] @ T[center]

                rf = torch.as_tensor(rf_cal[:, :, :, center], dtype=torch.float32)
                x, y, z = [grid[i].view(shape) for i in range(3)]
                z_proj = -torch.sqrt(y**2 + (z - self.ele_focus)**2) + self.ele_focus
                dist_tx = torch.abs(z_proj - tx_z)
                dist_rx = torch.sqrt((x-rx_pos[:,0,None,None])**2 + (y-rx_pos[:,1,None,None])**2 + (z-rx_pos[:,2,None,None])**2)
                tof = (dist_tx + dist_rx) / self.c

                rf_value = torch.zeros_like(dist_rx)
                for element in range(rx_pos.shape[0]):
                    rf_value[element] = su.linear_interp(dist_vector, rf[:, element], tof[element])

                env_center = torch.abs(su.hilbert(rf_value.sum(0)))
                trios.append((rf_cal, left, right, A_left_inv, A_right_inv, env_center))

        self.trios = trios[:num_trios]
        self.grid, self.shape, self.rx_pos = grid, shape, rx_pos
        self.tx_z, self.dist_vector = tx_z, dist_vector


    def forward(self):
        # Current calibration transform
        X = su.calibration_matrix(self.calibration)
        X_inv = torch.linalg.inv(X)
        losses = []

        # Calibration-dependent beamforming of the left and right frames
        for rf_cal, left, right, A_left_inv, A_right_inv, env_center in self.trios:

            for frame, A_inv in ((left, A_left_inv), (right, A_right_inv)):
                grid_local = (X_inv @ A_inv @ X) @ self.grid
                x, y, z = [grid_local[i].view(self.shape) for i in range(3)]

                z_proj = -torch.sqrt(y**2 + (z - self.ele_focus)**2) + self.ele_focus
                dist_tx = torch.abs(z_proj - self.tx_z)
                dist_rx = torch.sqrt((x-self.rx_pos[:,0,None,None])**2 + (y-self.rx_pos[:,1,None,None])**2 + (z-self.rx_pos[:,2,None,None])**2)
                tof = (dist_tx + dist_rx) / self.c

                rf = torch.as_tensor(rf_cal[:, :, :, frame], dtype=torch.float32)
                rf_value = torch.zeros_like(dist_rx)
                for element in range(self.rx_pos.shape[0]):
                    rf_value[element] = su.linear_interp(self.dist_vector, rf[:, element], tof[element])

                env = torch.abs(su.hilbert(rf_value.sum(0)))
                losses.append(su.corr2d_loss(env_center, env))

        return torch.stack(losses).mean()
