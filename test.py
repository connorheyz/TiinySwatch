import numpy as np

def deltaE2000_smoothed(Labstd, Labsample, KLCH=[1, 1, 1], smooth_factor=50):
    """
    Compute a 'smoothed' CIEDE2000 color difference between two Lab colors.
    
    This version is modified so that the hue‐dependent rotation term is less sensitive,
    thereby reducing sharp jumps in the computed difference. Note that this no longer
    exactly follows the published CIEDE2000, but may yield more stable perceptual ordering.
    
    Parameters
    ----------
    Labstd : array_like
        Reference Lab color as a 1D array-like: [L, a, b].
    Labsample : array_like
        Sample Lab color as a 1D array-like: [L, a, b].
    KLCH : list or tuple, optional
        Parametric factors [kL, kC, kH]. Defaults to [1, 1, 1].
    smooth_factor : float, optional
        Controls the width of the Gaussian in the rotation term.
        The standard uses 25; increasing this (e.g. to 50 or 100) softens the transition.
    
    Returns
    -------
    deltaE : float
        The (modified) CIEDE2000 color difference.
    """
    Labstd = np.array(Labstd, dtype=float)
    Labsample = np.array(Labsample, dtype=float)
    
    if Labstd.shape != (3,) or Labsample.shape != (3,):
        raise ValueError("Labstd and Labsample must be 1x3 vectors.")
    
    kl, kc, kh = KLCH

    # Unpack Lab values
    Lstd, astd, bstd = Labstd
    Lsample, asample, bsample = Labsample

    # Compute chroma for standard and sample (before adjustment)
    Cabstd = np.sqrt(astd**2 + bstd**2)
    Cabsample = np.sqrt(asample**2 + bsample**2)
    Cabarithmean = (Cabstd + Cabsample) / 2.0

    # Compute the G factor and adjust a values
    G = 0.5 * (1 - np.sqrt((Cabarithmean**7) / (Cabarithmean**7 + 25**7)))
    apstd = (1 + G) * astd
    apsample = (1 + G) * asample

    # Compute adjusted chroma values
    Cpstd = np.sqrt(apstd**2 + bstd**2)
    Cpsample = np.sqrt(apsample**2 + bsample**2)
    
    # Product of chromas and flag for zero chroma
    Cpprod = Cpstd * Cpsample
    zcidx = (Cpprod == 0)

    # Compute hue angles in radians for standard and sample.
    hpstd = np.arctan2(bstd, apstd)
    hpstd = np.where(hpstd < 0, hpstd + 2*np.pi, hpstd)
    hpstd = np.where((np.abs(apstd) + np.abs(bstd)) == 0, 0, hpstd)
    
    hpsample = np.arctan2(bsample, apsample)
    hpsample = np.where(hpsample < 0, hpsample + 2*np.pi, hpsample)
    hpsample = np.where((np.abs(apsample) + np.abs(bsample)) == 0, 0, hpsample)

    # Differences in L and chroma
    dL = Lsample - Lstd
    dC = Cpsample - Cpstd

    # Compute hue difference (in radians), ensuring it lies in [-pi, pi]
    dhp = hpsample - hpstd
    dhp = np.where(dhp > np.pi, dhp - 2*np.pi, dhp)
    dhp = np.where(dhp < -np.pi, dhp + 2*np.pi, dhp)
    dhp = np.where(zcidx, 0, dhp)
    
    # dH: hue difference component
    dH = 2 * np.sqrt(Cpprod) * np.sin(dhp/2)
    
    # Mean values of L and adjusted chroma
    Lp = (Lsample + Lstd) / 2.0
    Cp = (Cpstd + Cpsample) / 2.0

    # Mean hue (in radians)
    hp_mean = (hpstd + hpsample) / 2.0
    hp_mean = np.where(np.abs(hpstd - hpsample) > np.pi, hp_mean - np.pi, hp_mean)
    hp_mean = np.where(hp_mean < 0, hp_mean + 2*np.pi, hp_mean)
    hp_mean = np.where(zcidx, hpstd + hpsample, hp_mean)
    
    # Weighting functions
    Lpm502 = (Lp - 50)**2
    Sl = 1 + (0.015 * Lpm502) / np.sqrt(20 + Lpm502)
    Sc = 1 + 0.045 * Cp
    T = (1 - 0.17 * np.cos(hp_mean - np.pi/6) +
         0.24 * np.cos(2 * hp_mean) +
         0.32 * np.cos(3 * hp_mean + np.pi/30) -
         0.20 * np.cos(4 * hp_mean - 63*np.pi/180))
    Sh = 1 + 0.015 * Cp * T

    # Compute delta theta using the modified (smoothed) factor.
    # Note: The standard uses a divisor of 25; here we use smooth_factor.
    delthetarad = (30 * np.pi/180) * np.exp(- ((180/np.pi * hp_mean - 275)/smooth_factor)**2)
    Rc = 2 * np.sqrt((Cp**7) / (Cp**7 + 25**7))
    RT = - np.sin(2 * delthetarad) * Rc

    # Apply parametric factors and compute final delta E
    klSl = kl * Sl
    kcSc = kc * Sc
    khSh = kh * Sh

    deltaE = np.sqrt((dL/klSl)**2 +
                     (dC/kcSc)**2 +
                     (dH/khSh)**2 +
                     RT * (dC/kcSc) * (dH/khSh))
    return deltaE


# --- Example Usage ---
if __name__ == '__main__':
    # Two candidate colors.
    lab_lead = [56.09951596194911, -4.111263113733388, -5.0533580777297304]    # "lead" (dull gray)
    lab_superpink = [58.33940512035694, 46.004091208422025, -12.923211520384825]  # "super-pink"
    candidates = [lab_lead, lab_superpink]
    names = ['lead', 'super-pink']

    # Several target colors with gradually shifting b.
    targets = [
        [60.32364943499053, 98.23532017664644, -57.83500000000001],
        [60.32364943499053, 98.23532017664644, -58.83500000000001],
        [60.32364943499053, 98.23532017664644, -59.83500000000001],
        [60.32364943499053, 98.23532017664644, -60.83500000000001],
        [60.32364943499053, 98.23532017664644, -61.83500000000001],
        [60.32364943499053, 98.23532017664644, -62.83500000000001],
    ]

    for target in targets:
        distances = [deltaE2000_smoothed(candidate, target, smooth_factor=50) for candidate in candidates]
        best_idx = np.argmin(distances)
        print(f"Target: {target}")
        print(f"  Best match: {names[best_idx]} with smoothed ΔE₀₀ = {distances[best_idx]}")
